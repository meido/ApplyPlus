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

int print_switch( option_t option ) {

    if( option > 6 ) {
        printf( "Bad index %d.", option );
        return -1;
    }
    
    switch( option ) {

    case OPT_ONE:
        printf( "Found option 1.\n" );
        break;

    case OPT_TWO:
        printf( "Found option 2.\n" );
        break;

    case OPT_THREE:
        printf( "Found option 3.\n" );
        break;

    case OPT_FOUR:
        printf( "Found option 4.\n" );
        break;

    case OPT_FIVE:
        printf( "Found option 5.\n" );
        break;

    case OPT_SIX:
        printf( "Found option 6.\n" );
        break;

    default:
        printf( "Unknown option: %d\n", option );
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
