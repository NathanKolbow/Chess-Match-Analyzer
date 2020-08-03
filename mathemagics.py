from globals import OVERVIEW_GRAPH_DIVISOR
from math import log


"""
    Maps floats from -Inf to Inf (softmin/max -25/25) to proportions from -0.95 to 0.95 on a smooth, steep curve
"""
def Transform(eval):
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
    
    return [[a, ystart]] + points