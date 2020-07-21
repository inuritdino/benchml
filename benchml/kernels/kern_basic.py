import numpy as np
from ..pipeline import Transform

class KernelBase(object):
    def __init__(self, **kwargs):
        self.name = "base"
        self.X_fit = None
        self.K_fit = None
    def evaluate(self, X1, X2, symmetric, **kwargs):
        raise NotImplementedError("<evaluate> not defined")
    def evaluateFit(self, X, y='not_used', **kwargs):
        self.X_fit = X
        self.K_fit = self.evaluate(X, X, symmetric=True, **kwargs)
        return self.K_fit
    def evaluatePredict(self, X, **kwargs):
        return self.evaluate(X, self.X_fit, symmetric=False, **kwargs)

class KernelDotDeprecated(KernelBase):
    def __init__(self, **kwargs):
        KernelBase.__init__(self, **kwargs)
        self.power = kwargs["power"]
        self.name = "dot"
    def evaluate(self, X1, X2, symmetric='not_used', **kwargs):
        k = X1.dot(X2.T)
        k = k**self.power
        return k

class KernelDot(Transform):
    default_args = {'power': 1}
    req_inputs = ('X',)
    allow_params = {'X'}
    allow_stream = {'K'}
    stream_kernel = ('K',)
    precompute = True
    def evaluate(self, x1, x2=None):
        if x2 is None: x2 = x1
        return x1.dot(x2.T)**self.args["power"]
    def _fit(self, inputs):
        K = self.evaluate(inputs["X"])
        self.params().put("X", np.copy(inputs["X"]))
        self.stream().put("K", K)
    def _map(self, inputs):
        K = self.evaluate(inputs["X"], self.params().get("X"))
        self.stream().put("K", K)

class KernelGaussian(Transform):
    default_args = {'scale': 1}
    req_inputs = ('X',)
    allow_params = {'X','sigma'}
    allow_stream = {'K'}
    stream_kernel = ('K',)
    precompute = True
    def evaluate(self, x1, x2=None, sigma=None):
        x1s = x1/sigma
        z1 = np.sum(x1s**2, axis=1)
        if x2 is None:
            x2s = x1s
            z2 = z1
        else:
            x2s = x2/sigma
            z2 = np.sum(x2s**2, axis=1)
        zz = -0.5*np.add.outer(z1, z2)
        xx = x1s.dot(x2s.T)
        K = np.exp(zz+xx)
        return K
    def _fit(self, inputs):
        X = inputs["X"]
        sigma = self.args["scale"]*np.std(X, axis=0)
        K = self.evaluate(x1=inputs["X"], sigma=sigma)
        self.params().put("sigma", sigma)
        self.params().put("X", np.copy(inputs["X"]))
        self.stream().put("K", K)
    def _map(self, inputs):
        K = self.evaluate(x1=inputs["X"], x2=self.params().get("X"), 
            sigma=self.params().get("sigma"))
        self.stream().put("K", K)
