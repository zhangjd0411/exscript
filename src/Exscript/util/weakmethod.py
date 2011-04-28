# Copyright (C) 2007-2010 Samuel Abels.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 2, as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
"""
Weak references to bound and unbound methods.
"""
import weakref

class DeadMethodCalled(Exception):
    """
    Raised by L{WeakMethod} if it is called when the referenced object
    is already dead.
    """
    pass

class WeakMethod(object):
    """
    Do not create this class directly; use L{ref()} instead.
    """
    __slots__ = 'name', 'callback'

    def __init__(self, name, callback):
        """
        Constructor. Do not use directly, use L{ref()} instead.
        """
        self.name     = name
        self.callback = callback

    def _dead(self, ref):
        if self.callback is not None:
            self.callback(self)

    def get_function(self):
        """
        Returns the referenced method/function if it is still alive.
        Returns None otherwise.

        @rtype:  callable|None
        @return: The referenced function if it is still alive.
        """
        return None

    def isalive(self):
        """
        Returns True if the referenced function is still alive, False
        otherwise.

        @rtype:  bool
        @return: Whether the referenced function is still alive.
        """
        return self.get_function() is not None

    def __call__(self, *args, **kwargs):
        """
        Proxied to the underlying function or method. Raises L{DeadMethodCalled}
        if the referenced function is dead.

        @rtype:  object
        @return: Whatever the referenced function returned.
        """
        method = self.get_function()
        if method is None:
            raise DeadMethodCalled('method called on dead object ' + self.name)
        method(*args, **kwargs)

class _WeakMethodBound(WeakMethod):
    __slots__ = 'name', 'callback', 'f', 'c'

    def __init__(self, f, callback):
        name = f.__self__.__class__.__name__ + '.' + f.__func__.__name__
        WeakMethod.__init__(self, name, callback)
        self.f = f.__func__
        self.c = weakref.ref(f.__self__, self._dead)

    def get_function(self):
        cls = self.c()
        if cls is None:
            return None
        return getattr(cls, self.f.__name__)

class _WeakMethodFree(WeakMethod):
    __slots__ = 'name', 'callback', 'f'

    def __init__(self, f, callback):
        WeakMethod.__init__(self, f.__class__.__name__, callback)
        self.f = weakref.ref(f, self._dead)

    def get_function(self):
        return self.f()

def ref(function, callback = None):
    """
    Returns a weak reference to the given method or function.
    If the callback argument is not None, it is called as soon
    as the referenced function is garbage deleted.

    @type  function: callable
    @param function: The function to reference.
    @type  callback: callable
    @param callback: Called when the function dies.
    """
    try:
        function.__func__
    except AttributeError:
        return _WeakMethodFree(function, callback)
    return _WeakMethodBound(function, callback)
