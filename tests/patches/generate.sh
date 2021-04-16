#!/bin/bash

REVERSE=""
PATCHFILE=""
BACKUP=""

TEMP=$($(which getopt) -o ho:r --long help,output:,reverse -n "$0" -- "$@");
if [ $? != 0 ]; then
    echo "Invalid command line.  Exiting" >&2;
    exit 1;
fi

eval set -- "$TEMP"
unset TEMP

while true; do
    case "$1" in
        '-h'|'--help')
            cat <<EOF | fmt -s -w $(tput cols)
This script creates .patch files based on changes to the source file.

Options:
  -o <file> - Output patch to file <file>
  -r        - Reverse.  Instead of creating a patch that adds the new content, create a patch that removes the added content to get the original file.
  -b        - Create a backup (~) of the patch file
EOF
            shift
            exit 1;;
        '-r'|'--reverse')
            REVERSE="Yes"
            shift
            continue;;
        '-o'|'--output')
            PATCHFILE="$2"
            shift 2
            continue;;
        '-b'|'--backup')
            BACKUP="Yes"
            shift
            continue;;
        '--')
            shift
            break;;
        *)
            echo "Internal error." >&2
            exit 1;;
    esac
done

if [ -z "$PATCHFILE" ]; then
    echo "Missing output filename."
    exit 1;
fi

SRCFILES=("$@")

if [ "${#SRCFILES[@]}" == "0" ]; then
    SRCFILES=test.cpp
fi

dir=$(mktemp --tmpdir --directory 'generate-diff-XXXXXXXX')
for file in "${SRCFILES[@]}"; do
    cp "$file" "$dir/$(basename $file)"
done

PATCHFILE=$(realpath "$PATCHFILE")
if [ -f "$PATCHFILE" ]; then
    echo "Found pre-existing patch.  Applying it"
    pushd . >/dev/null
    cd "$dir"
    if [ -n "$REVERSE" ]; then
        patch -R -p2 < "$PATCHFILE"
    else
        patch -p2 < "$PATCHFILE"
    fi
    popd >/dev/null
fi

$EDITOR "$dir/"*

if [ -n "$BACKUP" ]; then
    cp "$PATCHFILE" "$PATCHFILE~"
fi

echo -n "" >"$PATCHFILE"
for file in "${SRCFILES[@]}"; do
    file=$(realpath "$file");
    pushd . >/dev/null
    cd ..
    if [ -n "$REVERSE" ]; then
        diff -Naup "$dir/$(basename $file)" "$file" >>"$PATCHFILE"
    else
        diff -Naup "$file" "$dir/$(basename $file)" >>"$PATCHFILE"
    fi
    popd >/dev/null
done

# Fix up the paths in the patch file.
if [ -n "$REVERSE" ]; then
    sed "s@$dir@a/patches@g; s@$(realpath .)@b/patches@g" -i "$PATCHFILE"
else
    sed "s@$dir@b/patches@g; s@$(realpath .)@a/patches@g" -i "$PATCHFILE"
fi

rm -rf "$dir"
