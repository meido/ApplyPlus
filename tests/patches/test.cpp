#include <string>
#include <memory.h>

typedef struct element_t {
    size_t length;
    size_t max_length;
    char buffer[80];
} element_t;

void copy_to_string( element_t &dst, const char * src ) {
    dst.length = strncpy( dst.buffer, src, dst.max_length );
    if( dst.length >= dst.max_length )
        dst.length = dst.max_length - 1;
    dst.buffer[dst.length] = '\0';
    return;
}

std::string MakeString( const char * str ) {
    char localString[256];
    memset( localString, 0, 256 );
    snprintf( localString, 256, "%s", str );

    printf( "Location of the string: %p\n", localString );

    return localString;
}

int main( int argc, char ** argv ) {
    if( argc < 1 ) {
        printf( "This isn't going to work.  I need an argument!\n" );
        return 1;
    }

    std::string value = MakeString( argv[1] );

    printf( "String: %s\n", value.c_str() );
    printf( "Location of the string: %p\n", value.c_str() );

    // Now, copy it into another buffer.
    element_t element;
    element.max_length = sizeof(element.buffer);

    copy_to_string( element, value.c_str() );

    printf( "String: %s\n", element.buffer );

    return 0;
}
