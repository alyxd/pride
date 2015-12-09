from math import ceil, sqrt

def is_prime(number):
    if not number % 2:
        return False
    for x in xrange(3, int(ceil(sqrt(number)))):
        if not number % x:
            print "Number divided evenly by: ", x
            return False
    else:
        return True
        
        
def prime_generator_start_at(number=3, _start_test_at=3):
    if not number % 2:
        number += 1# must be odd
    assert _start_test_at <= number
    composites = set()
    while True:
        for x in (x for x in xrange(_start_test_at, number) if x not in composites):
            if not number % x:
                break
        else:
            yield number
            composites.update([number * y for y in xrange(1, 11)])
        number += 2
        if number in composites:
            while number in composites:
                print "Incrementing to get out of composites...", number
                number += 2
            print "found an unknown number: ", number
            
def prime_generator(start=3, number=4, first_divisor=2, _lookahead_size=10):
    if not start % 2:
        start += 1# must be odd
    assert first_divisor < number, (first_divisor, number)
    assert start < number
    filter = set()
    for divisor in xrange(first_divisor, number):
        for _number in xrange(start, number, 2):
        #for _number in (_number for _number in xrange(start, number, 2) if _number not in filter):
    #        print "Checking if {} in {}".format(_number, filter)
            if _number not in filter:
                if _number == divisor:
                    yield _number
                    #filter.add(_number)
                    filter.update([_number * x for x in xrange(_lookahead_size)])
                    #for x in xrange(10):
                    #    filter.add(_number * x)
                elif not _number % divisor:
         #           print "Adding number to filter: ", _number
                    filter.add(_number)
        #for _number in (_number for _number in xrange(start, number, 2) if _number not in filter):
        #    if _number == divisor:
        #        yield _number
        #        filter.add(_number)
        #        for x in xrange(10):
        #            filter.add(_number*x)
        #    elif not _number % divisor:
        #        filter.add(_number)

        
def prime_factorization(number):
    #_number = int(ceil(sqrt(number))) # start here
   # print "Initial number: ", number
    prime_numbers = prime_generator_test()
   # _primes = set()
    divisor = next(prime_numbers)
    factors = []
    found = False
    while divisor < number:
  #      _primes.add(divisor)
        quotient, remainder = divmod(number, divisor)
        if quotient == 2:
            break
    #    print "{} / {} = {} + {}".format(number, divisor, quotient, remainder)
        if not remainder:
            _factors = prime_factorization(quotient)
            factor1, factor2 = next(_factors)
            yield (__factors, divisor)
            found = True
        try:
            divisor = next(prime_numbers)
        except StopIteration:
            break
    if not found:
        yield number
    #return factors
        
def prime_generator_test(_lookahead=3000, memory_allocation=100000000):
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
           # scalar[number] = (recalculate_at // number) or 1
           # if number >= recalculate_at:
           #     print "Recalculating composites...", number, recalculate_at
           #     composites = bytearray(memory_allocation)
           #     for prime in primes:
           #         _scalar = scalar[prime]
           #         for x in range(counter * _scalar, (1 + counter) * _scalar):
           #             composites[prime * x] = 1   
           #     recalculate_at += (2 * _lookahead)
           #     counter += 1
           #     print "...done", recalculate_at
           # else:
            for x in lookahead_range:
                composites[number * x] = 1

        
        ##if number not in composites:
        #prime = composites.index("\x00")
        #for x in lookahead_range:
        #    composites[prime * x] = 1
        #yield prime
      # # print "Returning prime: ", prime
      # # assert is_prime(prime), prime
        
        #if len(composites) >= _reallocate_threshold:
        #    print "Reallocating... "
        #    composites = set(sorted(list(composites))[len(composites) / 2:])
        #    #composites = set(_composites[_composites.index(number):])
        #    print "...done"
#print "14312312: ", prime_factorization(14312312) 
def test_generator():
    generator = prime_generator_test()#(number=1000)
    for x in xrange(1000):
        next(generator)
from pride.decorators import Timed
#print Timed(test_generator, 1)()
        
N = int(''.join(str(ord(char)) for char in 
        """MIGHAoGBAN01l"""))#Qw6DEtRySBBm+"""))#Sxl2ivcYmNB6UHovD1m4JOzZKXdHSg/V2S8j5q
        #8nb42Up17iYluPqTBxJH49JzoRqc3lGN4QtiSgQYI0DK9dkYlUIJcqdlYtcefhHH
        #w7hXtOHOTDx6ffAZaIx8j2BlmtQAZHqSBXRp0Uy4xPyfXMHdbP0DAgEC"""))        
#    print "\nfactors of {}: ".format(x), prime_factorization(x)    
print len(str(N)), N
for factors in prime_factorization(N):
    print factors