import pride.tests.attributetest 
Struct = pride.tests.attributetest.Struct
import pride.base
import pride.misc.decoratorlibrary
Timed = pride.misc.decoratorlibrary.Timed

from cPickle import dumps

base = pride.base.Base()
dictionary = base.__dict__
print "struct creation time: ", Timed(Struct, iterations=10000)(dictionary)
print "cpickle dumps time  : ", Timed(dumps, iterations=10000)(dictionary)