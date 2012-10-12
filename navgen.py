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

from panda3d.core import Geom, GeomVertexData, GeomVertexFormat, GeomVertexWriter, GeomTriangles, GeomNode

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
        
        # Note that this currently works with just a single vertex and color buffer and
        # and also just one GeomTriangles primitive that
        # we add more and more triangles to as we walk the mesh. No idea whether this is the best 
        # way to do this in Panda3d but for now it seems to work
        self.cell_vdata = GeomVertexData('DisplayCell', GeomVertexFormat.getV3c4(), Geom.UHDynamic)
        self.cell_vertex = GeomVertexWriter(self.cell_vdata, 'vertex')
        self.cell_color = GeomVertexWriter(self.cell_vdata, 'color')
        self.cell_primitives = GeomTriangles(Geom.UHDynamic)
        self.cell_geom = Geom(self.cell_vdata)
        self.cell_geom.addPrimitive(self.cell_primitives)
        self.cell_vertex_index = 0
        
        node = GeomNode('navmesh')
        node.addGeom(self.cell_geom)
        nodePath = render.attachNewNode(node)
        nodePath.setRenderModeWireframe()

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

        self.world_bounds = self.environ.getTightBounds()
        min = self.world_bounds[0]
        max = self.world_bounds[1]
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
        # we need to add a quad consisting of two triangles for the cell
        x = int(cell.world_pos.getX())
        y = int(cell.world_pos.getY())
        z = cell.world_pos.getZ()
        
        # vertex data
        quadsiz = 0.1
        height = z + 5.0
        
        self.cell_vertex.addData3f(x, y, height)
        self.cell_color.addData4f(1, 0, 0, 1)
        self.cell_vertex.addData3f(x+quadsiz, y, height)
        self.cell_color.addData4f(1, 0, 0, 1)
        self.cell_vertex.addData3f(x+quadsiz, y+quadsiz, height)
        self.cell_color.addData4f(1, 0, 0, 1)
        self.cell_vertex.addData3f(x, y+quadsiz, height)
        self.cell_color.addData4f(1, 0, 0, 1)
        
        # triangle primitives
        idx = self.cell_vertex_index
        self.cell_primitives.addVertices(idx+0, idx+1, idx+2)
        self.cell_primitives.addVertices(idx+0, idx+2, idx+3)
        self.cell_vertex_index += 4 
        
class Cell():
    def __init__(self, pos, i):
        self.world_pos = pos    # needed for display purposes
        self.grid_index = i     # index % grid_width = grid_x; index / grid_width = grid_y

        # print 'initializing new cell at index: '+str(i)
        
        # connectivity
        self.north = -1
        self.east = -1
        self.south = -1
        self.west = -1
    
class Walker():
    
    def __init__(self, navgen):
        self.navgen = navgen
        
    def walk(self, cell):
        # print 'walking cell:', cell.grid_index
        
        add_tasklist = []           # return new cells to add to tasklist
        x = cell.world_pos.getX()
        y = cell.world_pos.getY()
        
        # step north
        new_y = y + self.navgen.cell_size
        max_y = self.navgen.world.world_bounds[1][1]
        if(new_y <= max_y):
            # TODO implement actual "can move here" testing here
            # TODO determine the real Z by means of colission detection instead
            # of just copying the old cell's Z
            pos = Point3(x, new_y, cell.world_pos.getZ())
            idx = self.navgen.worldPosToGridIndex(pos)
            new_cell = Cell(pos, idx)       # create a new cell
            add_tasklist.append(new_cell)   # add new cell to tasklist
            cell.north = idx                # mark connectivity in existing cell
            
        return add_tasklist
        
            
class Navgen():
    
    def __init__(self, w):
        self.build_recursions = 0
        self.world = w
        self.task_list = []
        self.nav_grid = []
                
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
        c = Cell(w.start_pos, i)
        self.addCell(c)
        
        # init the Walker
        self.walker = Walker(self)
        
        
    # expects a Panda Point3d or Vec3d as input
    # returns a grid index
    def worldPosToGridIndex(self, world_pos):
        grid_index = int(world_pos.getX()/self.cell_size) + int(world_pos.getY()/self.cell_size) * self.grid_width
        return grid_index
        
    # add cell to the task_list ...
    def addCell(self, cell):
        self.task_list.append(cell)
        self.world.addDisplayCell(cell)
    
    # and remove it again    
    def removeCell(self, cell):
        self.task_list.remove(cell)
                
    # build the navmesh
    def build(self):
        self.build_recursions += 1
        rm_list = []
        for cell in self.task_list:
            add_list = self.walker.walk(cell)    # may add up to 4 new entries to navgrid
            rm_list.append(cell)                 # mark processed cell for removal from tasklist
                
        # remove cells processed this time around
        for cell in rm_list:
            self.removeCell(cell)
                
        # add new cells
        for cell in add_list:
            print 'adding new cell to tasklist; index=',cell.grid_index
            self.addCell(cell)
       
        # step Panda3d's task manager every once in a while so that the display updates etc.
        if (self.build_recursions % 10) == 0:
            taskMgr.step();

        if(len(self.task_list) > 0):
            self.build()
            

# ------------------------------------------------------------------------------
# main
# ------------------------------------------------------------------------------

print 'starting navgen v0.0.1'
w = World()
n = Navgen(w)
n.build()

while True:
    taskMgr.step();
    
    
    

