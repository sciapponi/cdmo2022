from pulp import *
import numpy as np
import inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
sys.path.insert(0, currentdir) 
import utils

class VLSI_Problem():

    def __init__(self,instance,rotationsAllowed=False):
        self.instance=instance
        self.rotationsAllowed=rotationsAllowed
        #PARAMETERS
        M=1000
        WC=instance["w"]
        n=instance["n"]
        dim=instance['dim']
        p=[i[0] for i in dim]
        q=[i[1] for i in dim]
        largest_idx=np.argmax([p[i]*q[i] for i in range(n)])
        tot_area=sum([w_i*h_i for w_i,h_i in zip(p,q)])
        stupidSol=utils.computeMostStupidSolution(instance,rotationsAllowed=rotationsAllowed)
        if not stupidSol:
            raise Exception("Feasibility check failed: No solution can exist to the problem. The object can not be built.")
        Hmin = tot_area/WC
        Hmax=stupidSol[0][1]
        # DECISION VARIABLES
        W=[] # Width of block
        H=[] # Height of block
        Xl=[] # left boundary of block
        Yb=[] # bottom boundary of block
        R=[] # 0 if block i is to the left of block j
        U=[] # 0 if block i is below block j
        F=[] # rotations
        
        HC=LpVariable(f"H_c",Hmin,Hmax,LpInteger)
        for i in range(n):
            Xl.append(LpVariable(f"Xl_{i}",0,None,LpInteger))
            Yb.append(LpVariable(f"Yb_{i}",0,None,LpInteger))
            if rotationsAllowed:
                W.append(LpVariable(f"W_{i}",0,None,LpInteger))
                H.append(LpVariable(f"H_{i}",0,None,LpInteger))
                F.append(LpVariable(f"F_{i}",0,1,LpInteger))
            else: 
                W.append(p[i])
                H.append(q[i])
                F.append(0)
            tempR=[]
            tempU=[]

            for j in range(n):
                if i!=j: 
                    tempR.append(LpVariable(f"R_{i}_{j}",0,1,LpInteger))
                    tempU.append(LpVariable(f"U_{i}_{j}",0,1,LpInteger))
                else:
                    tempR.append(None)
                    tempU.append(None)
            R.append(tempR)
            U.append(tempU)

        # CONSTRAINT REDUCTIONS
        
        for i in range(n):
            if not rotationsAllowed:
                if i!=largest_idx and  p[i]>(WC-p[largest_idx])/2:
                    R[i][largest_idx]=1
                for j in range(n):
                    if i!=j and p[i]+p[j]>WC: # Blocks are too wide together, cannot be stacked horizontally
                        R[i][j]=1
            if rotationsAllowed:
                if p[i]==q[i]: # Block is a square, avoid flipping
                    F[i]=0
            if i<j:
                if p[i]==p[j] and q[i]==p[j]: # Blocks have equal size, arbitrarily fix one to be in the low/left position   
                    R[i][j]=1 
                    U[i][j]=1 

        #if ws: warmStart(stupidSol,HC,Xl,Yb,R,U) # NON SO SE SERVE PORCODDI
        
        # PROBLEM FORMULATION    
        problem=LpProblem("VLSI_Problem", LpMinimize)

        problem += HC, "Chip_Height"
        problem += 2*Xl[largest_idx]<=WC-p[largest_idx], "Largest_rectangle_Xpos"
        problem += 2*Yb[largest_idx]<=HC-q[largest_idx], "Largest_rectangle_Ypos"
        for i in range(n):
            problem += W[i]== (1-F[i])*p[i] + F[i]*q[i], f"B_{i}_width"
            problem += H[i]== F[i]*p[i] + (1-F[i])*q[i], f"B_{i}_height"
            problem += Yb[i]+H[i]<=HC,  f"Max_{i}_Ypos"
            problem += Xl[i]+W[i]<=WC,  f"Max_{i}_Xpos"
            for j in range(n):
                problem += Xl[i]+W[i]-Xl[j]<=WC,  f"B_{i}_{j}_width_less_than_chip"
                problem += Yb[i]+H[i]-Yb[j]<=HC,  f"B_{i}_{j}_height_less_than_chip"

                if i!=j:
                    problem += Xl[i]+W[i]<=Xl[j]+M*R[i][j], f"B_{i}_{j}_non_overlap_horizontal"
                    problem += Yb[i]+H[i]<=Yb[j]+M*U[i][j], f"B_{i}_{j}_non_overlap_vertical"
                if i<j:
                    problem += R[i][j]+R[j][i]+U[i][j]+U[j][i]<=3, f"B_{i}_{j}_at_most_one_rel"                    

        self.variables={
            'WC':WC,
            'HC':HC,
            'X':Xl,
            'Y':Yb,
            'W':W,
            'H':H
        }
        self.problem=problem

    def solve(self,timeLimit=None,verbose=False):
        # BUILD SOLVER
        solver = getSolver('GUROBI', timeLimit=timeLimit,msg=verbose,gapRel=0)
        solver.buildSolverModel(self.problem)
        solver.callSolver(self.problem)
        solver.findSolutionValues(self.problem)
        
    def getElapsedTime(self):
        return self.problem.solverModel.RunTime
 
    def getStatusMessage(self):
        return LpStatus[self.problem.status]+ ("(or maybe time-out idk lol)" if self.problem.status==1 else "")
    
    def getStatusCode(self):
        return self.problem.solverModel.status

    def getSolution(self):
        solver_model=self.problem.solverModel
        if solver_model.SolCount > 0:
            h = solver_model.PoolObjVal
            vn=[var.VarName for var in solver_model.getVars()]
            vv=[var.X for var in solver_model.getVars()]
            solution=[[self.instance["w"],int(vv[vn.index("H_c")])]]
            for i in range(self.instance["n"]):
                if self.rotationsAllowed:
                    w=int(vv[vn.index(f"W_{i}")])
                    h=int(vv[vn.index(f"H_{i}")])
                else: 
                    w=self.instance['dim'][i][0]
                    h=self.instance['dim'][i][1]
                solution.append([w ,h \
                    ,int(vv[vn.index(f"Xl_{i}")])+1 ,int(vv[vn.index(f"Yb_{i}")])+1])
            return solution    
        else:
            return None

        # CPLEX
        # WC=self.variables['WC']
        # HC=self.variables['HC'].value()
        # X=[int(x.value()) for x in self.variables['X']]
        # Y=[int(y.value()) for y in self.variables['Y']]
        # if self.rotationsAllowed:
        #     W=[int(w.value()) for w in self.variables['W']]
        #     H=[int(h.value()) for h in self.variables['H']]
        # else:
        #     W=[w[0] for w in self.instance['dim']]
        #     H=[h[1] for h in self.instance['dim']]
        # solution=[[WC,HC]]+[[W[i],H[i],X[i]+1,Y[i]+1] for i in range(self.instance['n'])]

"""
# DEBUG
instance=utils.loadInstance("instances/ins-41.txt")
model=VLSI_Problem(instance,True)
sol=model.solve(timeLimit=2,verbose=True)
sol=model.getSolution()
print("Time:",model.getElapsedTime() ,"\nSOL:",sol)
if sol:
    utils.display_solution(sol)
"""