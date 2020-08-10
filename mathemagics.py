from globals import OVERVIEW_GRAPH_DIVISOR
from math import log

"""
    Basically clamps eval between (-1750, 1750) and linearly maps that range to (-95, 95)
"""
def TransformLinear(eval):
    if eval > 1750:
        return 95
    elif eval < -1750:
        return -95
    return eval * 0.0542857143 # (eval / 1750 * 95)


"""
    Maps floats from -Inf to Inf (softmin/max -25/25) to proportions from -95 to 95 on a smooth, steep curve
"""
def TransformNonlinear(eval):
    if eval == 0:
        return 0
    elif abs(eval) > 19.6:
        return 0.95 if eval > 0 else -0.95
    elif abs(eval) > 2:
        ret = 100*log(abs(eval), 50) + 19
    else:
        ret = 18.364*abs(eval)
    
    ret = min(95, ret)
    return ret/100 if eval > 0 else -ret/100


"""
# Based on integral((x/s-s)^2) where s = (3/2)^(1/4)
s = pow(3/2, 1/4)
def _antiderivative(x):
    #if x > 0:
    #    x += pow(s, 2)
    #    return (pow(x, 3) / (3*pow(s, 2))) - pow(x, 2) + pow(s, 2) * x

    #x = x + pow(s, 2)
    x += pow(s, 2)
    return (pow(x, 3) / (3*pow(s, 2))) - pow(x, 2) + pow(s, 2) * x


def ExpandCurve(a, b, ystart, yend):
    global s
    # Automatically finds a step that will be (somewhat) close to 1/OVERVIEW_GRAPH_DIVISOR and will be a whole number multiple of b-a
    length = b-a
    integer = 1

    while length/integer > 1:
        integer += 1
    step = (length / integer) / OVERVIEW_GRAPH_DIVISOR

    points = []
    x = a + step # skip 0 b/c it will always be (x, ystart)
    ycurr = ystart
    ytotal = 0
    
    total = 0
    while x <= b:
        x_s = (x - (a+b)/2) /(length/pow(s, 2))*2

        y = _antiderivative(x_s) - total
        total += y

        print("y: %s" % (y))

        x += step
        x = round(x, 4)
        ystep = (yend-ystart)*y
        ycurr += ystep
        
        if ystart > yend:
            points.append([x, min(ystart, max(yend, ycurr))])
        else:
            points.append([x, min(yend, max(ystart, ycurr))])
        
        ytotal += y
        
    print(ytotal)
    points[-1][1] = yend
    pts = []
    for point in points:
        pts.append(tuple(point))

    return [(a, ystart)] + pts
"""


# Based on integral(2-|4x|)
def ExpandCurve(a, b, ystart, yend):
    # Automatically finds a step that will be (somewhat) close to 1/OVERVIEW_GRAPH_DIVISOR and will be a whole number multiple of b-a
    length = b-a
    integer = 1

    while length/integer > 1:
        integer += 1
    step = (length / integer) / OVERVIEW_GRAPH_DIVISOR

    points = []
    x = a + step # skip 0 b/c it will always be (x, ystart)
    ycurr = ystart
    ytotal = 0
    
    while x <= b:
        if (x - a)/length - 0.5 > 0:
            y = (step/length)-2*(((x-a)/length)-0.5)*(step/length)-pow(step/length, 2)
        else:
            y = (step/length)+2*(((x-a)/length)-0.5)*(step/length)+pow(step/length, 2)
        y*=2
        
        if ystart > yend:
            points.append([x, min(ystart, max(yend, ycurr))])
        else:
            points.append([x, min(yend, max(ystart, ycurr))])

        x += step
        x = round(x, 4)
        ystep = (yend-ystart)*y
        ycurr += ystep
        
        ytotal += y
        
    points[-1][1] = yend
    pts = []
    for point in points:
        pts.append(tuple(point))

    return [(a, ystart)] + pts

"""
# Makes the curve linear
def ExpandCurve(a, b, ystart, yend):
    return([(a, ystart), (b, yend)])
"""