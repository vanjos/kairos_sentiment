#---------------------------------------------------------------
# Scenario:      Customers visit a bank with one counter.
#                Show the number of waiting customers and
#                the time average of that number over time.
# Model:         Make the counter a Resource. Use Matplotlib
#                to plot the data.
#---------------------------------------------------------------
import pylab as p
import random as ran

## Model components --------------------------------------------
from SimPy.SimulationRT import * 

class Visitor(Process):
    def visit(self,res,serveRate):
        yield request,self,res
        yield hold,self,ran.expovariate(serveRate)
        yield release,self,res

class VisitorGenerator(Process):
    def generate(self,arrRate,res,serveRate):
        while True:
            v = Visitor()
            activate(v,v.visit(res = res,serveRate = serveRate))
            yield hold,self,ran.expovariate(arrRate)

class Plotter(Process):
    def plotQ(self,tStep,res):
        moni = Monitor()
        p.ion()
        while now() < tEnd:
            yield hold,self,tStep
            moni.observe(len(res.waitQ))
            tAverage = moni.timeAverage()
            p.plot(moni.tseries(),moni.yseries(),"ro",
                   [now()],[tAverage],"b.")
            p.ylabel("nr waiting (time average = blue)")
            p.xlabel("time (hours)")
            p.title("Queuing customers. Time now = %s hours"%now())
            p.draw()

## Model --------------------------------------------------------
def bankModel(tStep,endTime,arrRate,serveRate,speed):
    res = Resource()
    initialize()
    vg=VisitorGenerator()
    activate(vg,vg.generate(arrRate = arrRate,res = res,serveRate = serveRate))
    pl=Plotter()
    activate(pl,pl.plotQ(tStep = tStep,res = res))
    simulate(until = endTime,real_time = True,rel_speed = speed)
           
## Experiment data ----------------------------------------------
arrRate = 10    # mean arrival rate of customers per hour
serveRate = 14  # mean service rate (customers per hour)
timeStep = 0.1  # plot update interval (simulation time units)
tEnd = 8        # run time (hours)
aniSpeed = 10   # ratio simulation time to real time
ran.seed(111777)

## Experiment and output ---------------------------------------
bankModel(tStep = timeStep,endTime = tEnd,speed = aniSpeed,
          arrRate = arrRate,serveRate = serveRate)
