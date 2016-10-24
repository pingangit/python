weakref 简单使用
==============

        练习 weakref 使用，掌握 weakref 使用场景和目的。
   [示例参考](http://sleepd.blog.51cto.com/3034090/1073044)
        
# 1. 概念

        首先需要了解的是在 Python 里每个对象都有一个引用计数，当这个引用计数为 0 时，Python 的 
    garbage collection(GC)是可以安全销毁这个对象的，比如对一个对象创建引用则计数加 1,删除引用
    则计数减 1 。
        
        weakref 模块允许对一个对象创建弱引用，弱引用不像正常引用，弱引用不会增加引用计数，也就是
    说当一个对象上只有弱引用时，GC是可以销毁该对象的。
    
        A primary use for weak references is to implement caches or mappings holding
    large objects, where it’s desired that a large object not be kept alive solely 
    because it appears in a cache or mapping.

# 2.1 weakref.ref

```
dbo@dbo-pc:~$ python
Python 2.7.12 (default, Jul  1 2016, 15:12:24) 
[GCC 5.4.0 20160609] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> 
>>> import weakref
>>> import sys
>>> class DBO(object):
...     pass
... 
>>> dbo1 = DBO()
>>> sys.getrefcount(dbo1)
2
>>> weakref_dbo = weakref.ref(dbo1)  # 创建弱引用
>>> sys.getrefcount(dbo1)  # 弱引用没有增加引用计数
2
>>> weakref_dbo  # 弱引用指向的对象
<weakref at 0x7f9b0316d3c0; to 'DBO' at 0x7f9b03166ed0>
>>> dbo2 = weakref_dbo()  # 获取弱引用指向的对象
>>> dbo1 is dbo2  # dbo1和dbo2引用的是同一个对象
True
>>> sys.getrefcount(dbo1)  # 对象上的引用计数加 1
3
>>> sys.getrefcount(dbo2)
3
>>> dbo1 = None  # 删除引用
>>> sys.getrefcount(dbo1)  # 这里不明白为什么是这个数字
2545
>>> sys.getrefcount(None)  # None 的计数是 2546，python2 和 python3 不一样
2546
>>> 
>>> weakref_dbo
<weakref at 0x7f9b0316d3c0; to 'DBO' at 0x7f9b03166ed0>
>>> dbo2 = None  # 删除引用
>>> weakref_dbo  # 当对象引用计数为0时，弱引用失效
<weakref at 0x7f9b0316d3c0; dead>
>>> sys.getrefcount(dbo1)
2546
>>> 
```

# 2.2 weakref.proxy
        proxy 像是弱引用对象，它们的行为就是它们所引用的对象的行为，这样就不必首先调用弱引用对象
    来访问背后的对象。
```
>>> from socket import *
>>> s = socket(AF_INET, SOCK_STREAM)
>>> ref_s = weakref.ref(s)
>>> ref_s
<weakref at 0x7f9b0316d3c0; to '_socketobject' at 0x7f9b0310b910>
>>> s
<socket._socketobject object at 0x7f9b0310b910>
>>> proxy_s = weakref.proxy(s)
>>> proxy_s
<weakproxy at 0x7f9b03117208 to _socketobject at 0x7f9b0310b910>
>>> 
>>> ref_s.close()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'weakref' object has no attribute 'close'
>>> ref_s().close()  #  不能直接调用对象方法，要加上()
>>>
>>> proxy_s.close()  #  可以直接调用对象方法
>>> 
>>> sys.getrefcount(s)
2
>>> ref_s
<weakref at 0x7f9b0316d3c0; to '_socketobject' at 0x7f9b0310b910>
>>> r = ref_s()
>>> r.close()
>>> sys.getrefcount(s)
3
>>> ref_s
<weakref at 0x7f9b0316d3c0; to '_socketobject' at 0x7f9b0310b910>
>>> del ref_s
>>> ref_s
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
NameError: name 'ref_s' is not defined
>>> 

```