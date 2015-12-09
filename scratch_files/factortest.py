from math import ceil, sqrt

def convert(old_value, old_base, new_base):
    old_base_size = len(old_base)
    new_base_size = len(new_base)
    old_base_mapping = dict((symbol, index) for index, symbol in enumerate(old_base))
    decimal_value = 0    
    new_value = ''
    
    for power, value_representation in enumerate(reversed(old_value)):
        decimal_value += old_base_mapping[value_representation]*(old_base_size**power)
                            
    if decimal_value == 0:
        new_value = new_base[0]
    else:
        while decimal_value > 0: # divmod = divide and modulo in one action
            decimal_value, digit = divmod(decimal_value, new_base_size)
            new_value += new_base[digit]

    return ''.join(reversed(new_value))
    
def is_prime(number):
    if not number % 2:
        return False
    for x in xrange(3, int(ceil(sqrt(number)))):
        if not number % x:
            print "Number divided evenly by: ", x
            return False
    else:
        return True
        
def prime_generator(_lookahead=30000, memory_allocation=1000000000):
    """ Generates prime numbers by generating composite numbers from the first
        few primes, then searching through the result. Numbers that are not 
        members of the set of composite numbers are prime.
        
        The set of composite numbers is generated by multiplying each found prime
        by each number from 2 to _lookahead. There may be a precise ideal value for
        this setting. Setting it too low will result in inaccurate results."""
    # basically, just scan through the odd numbers, looking for ones that aren't composite
    composites = bytearray(memory_allocation)
    composites[:2] = "\x01\x01"
    lookahead_range = range(1, _lookahead, 2)
    for x in range(1, _lookahead):
        composites[2 * x] = 1
    for x in lookahead_range:
        composites[3 * x] = 1
    #for prime in (2, 3):
    #    for x in lookahead_range:
    #        composites[prime * x] = 1
    recalculate_at = 2 * _lookahead
    yield 2
    yield 3
    number = 3
    #print [char for char in composites if char]
    primes = []
    scalar = {}
    counter = 0
    while True:
        number += 2            
        if not composites[number]:
            assert is_prime(number), number
            yield number
            primes.append(number)
            for x in lookahead_range:
                composites[number * x] = 1
                
def factor(number):
    result = bytearray(4096)
    #if number % 2:
    #    number += 1
    #    result[0] = 1
    for index, prime in enumerate(prime_generator()):
        power = 0
        while True:
    #        print "Dividing {} / {}".format(number, prime)
            number, remainder = divmod(number, prime)
    #        print "Result: ", number, remainder
            if remainder:
    #            print "Breaking because of remainder"
                number *= prime # undo the assignment above
                number += remainder
                break
            power += 1
            if number == 1:
                break
     #   print "Setting index {} prime {} to power {}".format(index, prime, power)
        result[index] = power
        if number == 1:
            break
    return [power for power in result[:index + 1]]
    
def compress(number):
    result = bytearray(4096)
    power = 0
    #while True:
    for index, prime in enumerate(prime_generator()):
        print "Removing chunk from: ", number, prime
        while (prime ** power) < number:
            power += 1
            if power == 256:
                break
        assert prime ** (power - 1) <= number
        power -= 1
        print "Set value to: ", prime, power
        result[index + 1] = power  
        number -= prime ** power
        if number <= 256:
            print "Setting remainder: ", number
            result[0] = number
            break
        power = 0
    return result[:index + 2]
            
#126
#63 * 2 ** 1
#21 * 3 * 2 ** 1
#7 ** 1 * 3 ** 2 * 2 ** 1
#
#1 2 3 5 7 11 13 17 19
#1 1 2 0 1 


_primes = prime_generator()
#base_prime = ''.join(chr(next(_primes)) for x in xrange(54))
#print base_prime, [ord(char) for char in base_prime]
if __name__ == "__main__":
    #primes = prime_generator()
    factor_me = int(''.join(format(ord(character), 'b').zfill(8) for character in "test" * 5), 2)
    #print len(str(factor_me)), factor_me
    #converted = convert(str(factor_me), "0123456789", base_prime)
    #print converted
    #converted_back = convert(converted, base_prime, "0123456789")
    #print converted_back
    #assert factor_me == int(converted_back)
    #print " * ".join(["{} ** {}".format(next(primes), power) for power in factor(factor_me)])
    results = compress(factor_me)
    #remainder = results[0]
    calculation = results[0]
    
    for value in results[1:]:
        calculation += next(_primes) ** value
    assert calculation == 102500, calculation
    print len(results), len(results) * 8, len(format(102500, 'b').zfill(8))