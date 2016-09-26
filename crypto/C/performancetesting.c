#include <time.h>
#include <stdio.h>

#include "constants.c"

#define test_encrypt_performance_4x32(cipher_encrypt, measurements)\
({	WORDSIZE32 message[4], key[4];\
    unsigned long index;\
    clock_t begin = clock();\
    for (index = 0; index < measurements; index++){\
	    cipher_encrypt(message, key);}\
    clock_t end = clock();\
    double time_spent = (double)(end - begin) / CLOCKS_PER_SEC;\
    printf("Time required: %.2fs\n", time_spent);\
})

#define test_encrypt_performance_2x32(cipher_encrypt, measurements)\
({	WORDSIZE32 message[2], key[2];\
    unsigned long index;\
    clock_t begin = clock();\
    for (index = 0; index < measurements; index++){\
	    cipher_encrypt(message, key);}\
    clock_t end = clock();\
    double time_spent = (double)(end - begin) / CLOCKS_PER_SEC;\
    printf("Time required: %.2fs\n", time_spent);\
})
