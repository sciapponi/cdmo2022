from z3 import *
from time import time
import numpy as np
import os,sys 
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
sys.path.insert(0, currentdir) 
import utils

def format_solution(m, o, dim, n, W):

    schema = []
    if m != None:
        nicer = sorted ([(d, m[d]) for d in m], key = lambda x: str(x[0]))
        dict = {str(l[0]):l[1] for l in nicer if str(l[0]).startswith("x__") or str(l[0]).startswith("y__")}

        blockpos = []
        for i in range(n):
            blockpos.append([int(str(dict['x__{}'.format(i)]))+1,int(str(dict['y__{}'.format(i)]))+1])

        schema = [[W,o]]

        for i in range(n):
            schema.append([*dim[i], *blockpos[i]])

    return schema


def no_overlap(Xs, Ys, Ws, Hs, W, H, n):
    no = [ Or(
                And(
                    Xs[i] + Ws[i] <= Xs[j], 
                    Xs[i] - Ws[j] >= Xs[j] - W, 
                    Ys[i] + Hs[i] <= Ys[j] + H, 
                    Ys[i] - Hs[j] >= Ys[j] - 2*H),
                And(
                    Xs[i] + Ws[i] <= Xs[j] + W, 
                    Xs[i] - Ws[j] >= Xs[j] - 2*W, 
                    Ys[i] + Hs[i] <= Ys[j], 
                    Ys[i] - Hs[j] >= Ys[j] - H),
                And(
                    Xs[i] + Ws[i] <= Xs[j] + W, 
                    Xs[i] - Ws[j] >= Xs[j], 
                    Ys[i] + Hs[i] <= Ys[j] + 2*H, 
                    Ys[i] - Hs[j] >= Ys[j] - H),
                And(
                    Xs[i] + Ws[i] <= Xs[j] + 2*W, 
                    Xs[i] - Ws[j] >= Xs[j] - W, 
                    Ys[i] + Hs[i] <= Ys[j] + H, 
                    Ys[i] - Hs[j] >= Ys[j])
                ) for i in range(n) for j in range(n) if i!=j ]

    return no


def buildModel(instance, o):
    n = instance['n']
    w = instance['w']
    dim = instance['dim']

    #Largest block symmetry break
    largest_block = np.argmax([d[0]*d[1] for d in dim ])

    # Height: sum of all blocks heights
    H = sum([int(dim[i][1]) for i in range(n)])

    # Width: silicon plate width
    W = w

    # Block Position Vectors
    X = IntVector('x', n)
    Y = IntVector('y', n)


    # Block widths and heights
    widths = [d[0] for d in dim]
    heights = [d[1] for d in dim]

    # Height variable
    d = o
    
    #Solver Declaration
    s = Tactic('lra').solver()

    #Boundary
    # Max X Domain
    s.add([And(0 <= X[i], X[i] <= W-widths[i]) 
            if i!=largest_block else And(0 <= X[i], X[i] <= int(W-widths[i])/2) 
            for i in range(n)])
    # Max Y Domain
    s.add([And(0 <= Y[i], Y[i] <= d-heights[i]) 
            if i!=largest_block else And(0 <= Y[i], Y[i] <= int(d-heights[i])/2) 
            for i in range(n)])

    no = no_overlap(X, Y, widths, heights, W, H, n)
    s.add(no)
    return s
    
def bisection(instance, timeout=None,verbose=False):
    init = time()

    naiive = utils.computeMostStupidSolution(instance)
    if not naiive:
        return None,None,None

    LB = int(sum([p[0]*p[1] for p in instance['dim']])/instance['w'])
    UB = naiive[0][1]+1

    m=None
    o = int((LB+UB)/2)
    best_o=o=UB

    if verbose:
        print("BISECTION STARTING VALUES:")
        print('lb', LB)
        print('ub', UB)
        print("o", o)
        print("-----------------------")
    
    while LB<UB:
        s = buildModel(instance, o)
        if timeout and (time()-init>timeout+1):
            break
        if timeout: set_option(timeout=int(timeout+init-time())*1000)
        if(s.check() == sat):
            best_o=o
            UB = o
            m = s.model()        
            if verbose:
                print("sat, UB:", UB)
        else:
            LB = o +1
            if verbose:
                print("unsat, LB:", LB)
        o = int((LB+UB)/2)
        if verbose:
            print("o:", o)
            print("-----------------------")

    return best_o, m, time()-init


def solveInstance(instance, options):
    # Solve the instance
    o, m, t = bisection(instance,options["timeout"],options['verbose'])
    if options["timeout"] and t>options["timeout"]:  print("Time limit reached")
    if m:
        sol=format_solution(m, o, instance['dim'], instance['n'], instance['w'])
        print("Instance solved")
        if options["verbose"]: print("Minimum Height Found: ", o)
        print("Instance Model:", sol)
        if options["verbose"]: print("Solved in: {}s".format(t))
        print("-----------------------")
        # Write out the solutions
        if options['output']:
            utils.writeSolution(options['output'],sol)
        # Plot the solution
        if options['show']:
            utils.display_solution(sol)
    else: print("No solution found!")

def main():
    # report
    filename=currentdir+"/report.csv"
    with open(filename, 'w') as outfile:
        outfile.write("Instance;Time;Solution\n")
    for i in range(1,41):
        print("SOLVING: ", i)
        instance = utils.loadInstance(currentdir+f"/../instances/ins-{i}.txt")

        print(instance)
        o, m, t = bisection(instance,300)

        m = format_solution(m, o, instance['dim'], instance['n'], instance['w'])
        print(m)

        if(t<300):
            with open(filename, 'a') as outfile:
                outfile.write("{};{};{}\n".format(i,t,m))
        else:
            with open(filename, 'a') as outfile:
                outfile.write("{};{};{}\n".format(i,t,m))
        print("Finished in:", t)

if __name__=="__main__":
    main()
