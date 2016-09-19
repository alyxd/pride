#include <time.h>
#include <string.h>
#include <stdio.h>

#define WORDSIZE unsigned long

void test_encrypt_performance(void (*cipher_encrypt)(WORDSIZE*, WORDSIZE*), 
                                int input_size, unsigned long byte_count, int block_size) 
{
	WORDSIZE message[input_size], key[input_size];
    memset(message, 0, input_size);
    memset(key, 0, input_size);
    key[0] = 1;
  		
    WORDSIZE index, measurements = byte_count / block_size;
    clock_t begin = clock();
	for (index = 0; index < measurements; index++) 
    {
	    cipher_encrypt(message, key);            
	}        	    
    clock_t end = clock();
    double time_spent = (double)(end - begin) / CLOCKS_PER_SEC;    
    printf("Time required: %.2fs\n", time_spent);
}

void test_permutation_performance(void (*permutation)(WORDSIZE*), 
                                  int input_size, unsigned long byte_count, int block_size) 
{
	WORDSIZE message[input_size];
    memset(message, 0, input_size);
    message[0] = 1;
  		
    WORDSIZE index, measurements = byte_count / block_size;
    clock_t begin = clock();
	for (index = 0; index < measurements; index++) 
    {	            
        permutation(message);
	}        	    
    clock_t end = clock();
    double time_spent = (double)(end - begin) / CLOCKS_PER_SEC;    
    printf("Time required: %.2fs\n", time_spent);
}