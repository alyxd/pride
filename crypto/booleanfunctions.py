import sys
import pprint

from cryptanalysis import summarize_sbox
from utilities import integer_to_bytes

def choice(b, c, d):
    return d ^ (b & (c ^ d))
    
def majority(b, c, d):
    return (b & c) | (b & d) | (c & d)     
    
def test_choice():
    sbox = {(_input, choice(*_input)) for _input in (tuple(bytearray(integer_to_bytes(integer, 3))) for integer in xrange(2 ** 24))}
    print "Done "
    with open("choice_sbox.txt", 'w') as _file:
        _file.write(pprint.pformat(sbox))
   # for integer in range(2 ** 24):
   #     _input = tuple(bytearray(integer_to_bytes(integer, 3)))
   #     sbox[_input] = choice(*_input)
    
    summarize_sbox(sbox)
    
if __name__ == "__main__":
    test_choice()
    