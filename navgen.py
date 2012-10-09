'''
navgen
0.0.1
gsk October 2012

navigation map generator for NetRalph
'''

import direct.directbase.DirectStart

from panda3d.core import TextNode
from panda3d.core import Filename,AmbientLight,DirectionalLight
from panda3d.core import Vec3, Vec4, Point3
from panda3d.core import GeomVertexData, GeomVertexFormat, GeomVertexWriter, Geom

from direct.gui.OnscreenText import OnscreenText
from direct.actor.Actor import Actor
from direct.showbase.DirectObject import DirectObject
from pandac.PandaModules import WindowProperties

import sys

VERSION = '0.0.1'

# Function to put instructions on the screen.
def addInstructions(pos, msg):
    return OnscreenText(text=msg, style=1, fg=(1,1,1,1),
                        pos=(-1.3, pos), align=TextNode.ALeft, scale = .05)

# Function to put title on the screen.
def addTitle(text):
    return OnscreenText(text=text, style=1, fg=(1,1,1,1),
                        pos=(1.3,-0.95), align=TextNode.ARight, scale = .07)



class World(DirectObject):

    def __init__(self):
        
        print 'world initializing'

        # navmesh cell display data structures
        self.cell_vdata = GeomVertexData('DisplayCell', GeomVertexFormat.getV3c4(), Geom.UHStatic)
        self.cell_vertex = GeomVertexWriter(self.cell_vdata, 'vertex')
        self.cell_color = GeomVertexWriter(self.cell_vdata, 'color')
        
        # application window setup
        base.win.setClearColor(Vec4(0,0,0,1))
        props = WindowProperties( )
        props.setTitle( 'navgen' )
        base.win.requestProperties( props ) 
        
        # Post the instructions
        self.title = addTitle('navgen v.' + VERSION)
        self.inst1 = addInstructions(0.95, "[ESC]: Quit")
        
        # Set up the environment
        #
        # This environment model contains collision meshes.  If you look
        # in the egg file, you will see the following:
        #
        #    <Collide> { Polyset keep descend }
        #
        # This tag causes the following mesh to be converted to a collision
        # mesh -- a mesh which is optimized for collision, not rendering.
        # It also keeps the original mesh, so there are now two copies ---
        # one optimized for rendering, one for collisions.  
        self.environ = loader.loadModel("models/world")      
        self.environ.reparentTo(render)
        self.environ.setPos(0,0,0)

        world_bounds = self.environ.getTightBounds()
        min = world_bounds[0]
        max = world_bounds[1]
        self.xsize = max[0] - min[0]
        self.ysize = max[1] - min[1]
        self.campos = Point3(min[0] + self.xsize/2, min[1] + self.ysize/2, 350.0)
        
        print 'world size x =', self.xsize, ' y =', self.ysize
        
        self.start_pos = self.environ.find("**/start_point").getPos()
        print "start pos:", self.start_pos
        
        # Accept the application control keys: currently just esc to exit navgen 
        self.accept("escape", self.exitGame)

        # Create some lighting
        ambientLight = AmbientLight("ambientLight")
        ambientLight.setColor(Vec4(.3, .3, .3, 1))
        directionalLight = DirectionalLight("directionalLight")
        directionalLight.setDirection(Vec3(-5, -5, -5))
        directionalLight.setColor(Vec4(1, 1, 1, 1))
        directionalLight.setSpecularColor(Vec4(1, 1, 1, 1))
        render.setLight(render.attachNewNode(ambientLight))
        render.setLight(render.attachNewNode(directionalLight))

        taskMgr.add(self.dummyTask, "dummyTask")

    def dummyTask(self, task):
        base.camera.setPos(self.campos)
        base.camera.lookAt(Point3(self.campos.getX(), self.campos.getY(), 0.0), Vec3(0.0, 1.0, 0.0))
        return task.cont
        
    def exitGame(self):           
        sys.exit(0)
                
    #Records the state of the arrow keys
    # this is used for camera control
    def setKey(self, key, value):
        self.keyMap[key] = value

    def addDisplayCell(self, cell):
        pass
        
        
class Cell():
    def __init__(self, i = -1):
        self.grid_index = i
        self.north = -1
        self.east = -1
        self.south = -1
        self.north = -1
    

class Navgen():
    
    def __init__(self, w):
        self.world = w
        self.task_list = []
        
        # determine grid 
        self.cell_size = 0.1
        self.grid_width = int(w.xsize/self.cell_size)
        self.grid_height = int(w.ysize/self.cell_size)
        self.num_cells = self.grid_width * self.grid_height
        print 'navgen initializing'
        print 'cell_size: ', self.cell_size
        print 'grid width,height: ', self.grid_width, self.grid_height
        print 'num_cells: ', self.num_cells
        
        # init task list with the start cell determined from the world start_pos
        i = self.worldPosToGridIndex(w.start_pos)
        print 'start cell: ', i
        c = Cell(i)
        self.addCell(c)
        
    # expects a Panda Point3d or Vec3d as input
    # returns a grid index
    def worldPosToGridIndex(self, world_pos):
        grid_index = int(world_pos.getX()/self.cell_size) + int(self.world.start_pos.getY()/self.cell_size) * self.grid_width
        return grid_index
        
    # add a "walkable" cell to the task list
    def addCell(self, cell):
        self.task_list.append(cell)
        self.world.addDisplayCell(cell)
        
    # build the navmesh
    def build(self):
        while(len(self.task_list) > 0):
            taskMgr.step();


# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

print 'starting navgen v0.0.1'
w = World()
n = Navgen(w)
n.build()

    
    

