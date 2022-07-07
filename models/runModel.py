import getopt,sys,os,inspect
import utils
import SMT.vlsi_SMT as SMT
import MIP.vlsi_MINLP as LP
import CP.vlsi_CP as CP
import warnings
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
warnings.filterwarnings("error")

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "ho:rvi:t:", ["help","input=","instn=", "output=","export=","timeout=","show-result"])
    except getopt.GetoptError as err:
        print(err)
        usage()
        sys.exit(2)

    input=None
    output = None # file to which export the solution
    export= None # file to which export the model
    verbose = False
    show=False
    rotationsAllowed=False
    timeout=None 
    instn=None

    for o, a in opts:
        if o == "-v":
            verbose = True
        elif o == "-r":
            rotationsAllowed = True 
        elif o == "--show-result":
            show = True        
        elif o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-o", "--output"):
            output = a
        elif o in ("-t","--timeout"):
            try: timeout=int(a)
            except Exception as e: 
                print(e)
                sys.exit(2) 
        elif o in ("--export"):
            export = a
        elif o in("-i","--input"):
            input=a
        elif o in ("--instn"):
            try: 
                instn=int(a)
                if instn<1 or instn> 40: raise Exception
            except Exception as e:
                print("Error: instn must be an integer between 1 and 40")
                usage()
                sys.exit(2)
        else:
            assert False, "unhandled option \"{}\"".format(o)
    
    if input and instn:
        print("Error: you should specify either an instance number or an input file, not both")
        usage()
        sys.exit(2)
    if instn:
        input=currentdir+f"/instances/ins-{instn}.txt"

    # Check if model name is valid
    if(len(args)!=1):
        print("Error: you must specify a model")
        usage()
        sys.exit(2)

    model=args[0].upper()
    if model not in ["CP","SAT","SMT","ILP"]:
        print("Error: solving strategy \"{}\" not recognized. Allowed names are \"CP\",\"SAT\"\"SMT\"\"ILP\"".format(model))
        sys.exit(2)

    #load problem instance
    instance=utils.loadInstance(input)

    # Print useful informations
    print("Solving instance: {}".format(instn))
    print(f"Solving strategy: {model}")
    print("Rotations: "+("allowed" if rotationsAllowed else "not allowed"))
    print("Timeout: {}".format(f"{timeout}s" if timeout else "not set"))
    if verbose: print("Verbose output activated")

    # Build options
    options={
        "verbose":verbose,
        "timeout":timeout,
        "output":output,
        "show": show,
        "rotationsAllowed":rotationsAllowed,
        "export":export
    }

    # Solver run functions
    func={
        "CP":runCPInstance,
        "SAT":runSATInstance,
        "SMT":runSMTInstance,
        "ILP":runILPInstance
    }
    
    # Run the solver
    run=func[model]
    run(instance,options)

def usage(): 
    print("Usage: python {} [-i instn] [-t timeout] [-v] [-o outfile] <strategy>".format(sys.argv[0]))

def runCPInstance(instance,options):
    CP.solveInstance(instance,options)

def runSATInstance(instance,options):
    pass

def runSMTInstance(instance,options):
    SMT.solveInstance(instance,options)

def runILPInstance(instance,options):
    LP.solveInstance(instance,options)

if __name__=="__main__":
    main()