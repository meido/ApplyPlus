#include <stdio.h>
#include <stdlib.h>

enum option_t {
    OPT_ONE,
    OPT_TWO,
    OPT_THREE,
    OPT_FOUR,
    OPT_FIVE,
    OPT_SIX,
};

#define SHOW_ERROR0(x) printf( "%s\n", x )

int print_switch( option_t option, int value ) {

    if (value >= 7) {
        SHOW_ERROR( "print_switch (): Bad option" );
        return 1;
    }

    switch( option ) {

    case OPT_ONE:
        if (value != 1) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    case OPT_TWO:
        if (value != 2) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    case OPT_THREE:
        if (value != 3) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    case OPT_FOUR:
        if (value != 4) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    case OPT_FIVE:
        if (value != 5) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    case OPT_SIX:
        if (value != 6) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        break;

    default:
        if (value != 0) {
            SHOW_ERROR( "print_switch (): Bad option" );
            return 1;
        }
        value += 100;
        break;
    }
    return 0;
}

int main( int argc, char ** argv ) {
    if( argc < 2 ) {
        fprintf( stderr, "Missing argument.\n" );
        return 1;
    }

    option_t option = (option_t)atoi( argv[1] );
    print_switch( option );
    return 0;
}
