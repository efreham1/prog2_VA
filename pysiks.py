from aifc import Error
import numpy as np

class Physics_Canvas:
    
    def __init__(self, w, h, walls, res) -> None:
        if w%2 == 0 or h%2 == 0 or res%2 == 0 :
            raise Error('Even width and/or height and/or resolution is unsupported')
        self.width = w
        self.height = h
        self.res = res
        self.matrix = self.matrix_generator(walls) #[[[w0, w1], [w2, w3]...], [[h0, h1]...], [[w0, w1]...], [[h0, h1]...]] starts at top goes anti-clockwise always left to right and up to down
        self.rect_names = {}
        self.rects = []

    def __str__(self) -> str:
        return str(self.matrix)
        

    def matrix_generator(self, walls):
        matrix = np.full((self.height*self.res+2, self.width*self.res+2), ' ')
        slicer = {
            0 : matrix[0],
            1 : matrix[:, -1],
            2 : matrix[-1],
            3 : matrix[:, 0]
        }
        for i, e in enumerate(walls):
            for ee in e:
                if ee != []:
                    for n in range(len(slicer[i])):
                        if n in range((ee[0]-1)*self.res+1, ee[1]*self.res+1):
                            slicer[i][n] = 'b'
                        else:
                            slicer[i][n] = 'w'
        return matrix

    def matrix_cord(self, x, y):
        return (self.height//2+1+y, self.width//2+1+x)

    def vector_to_matrix(self, name, *vectors):
        for vector in vectors:
            vector *= self.res
            vector = np.round_(vector)


    class rectangle:

        def __init__(self, w, h, m):
            self.width = w
            self.height = h
            self.mass = m
            self.momI = 1/12*3*(w**2+h**2)
            self.pos = np.zeros(2)
            self.vel = np.zeros(2)
            self.angle = 0
            self.angle_vel = 0
            self.corners = self.cal_corners()
        
        def cal_corners(self):
            r = (self.width**2+self.height**2)/4
            a = np.tan(self.height/self.width)
            return [
                r*np.array([np.cos(a+self.angle), np.sin(a+self.angle)]),
                r*np.array([np.cos(np.pi-a+self.angle), np.sin(np.pi-a+self.angle)]),
                r*np.array([np.cos(np.pi+a+self.angle), np.sin(np.pi+a+self.angle)]),
                r*np.array([np.cos(2*np.pi-a+self.angle), np.sin(2*np.pi-a+self.angle)])
                ] #start at top right goes anti-clockwise


        def move_to(self, x, y):
            self.pos = np.array([x,y])
            self.corners = self.cal_corners()
            return self.corners
        
        def rotate_to(self, theta):
            self.angle = theta
            self.corners = self.cal_corners()
            return self.corners
    
    def gen_rect(self, name, w, h, m):
        self.rects.append(self.rectangle(w, h, m))
        self.rect_names[name] = len(self.rects)-1

    
    def move_rect(self, name, x, y):
        try:
            self.rects[self.rect_names[name]].move_to(x,y)
        except KeyError:
            raise Error(f'There is no rectangle by the name {name}')

    
    def rotate_rect(self, name, theta):
        try:
            self.rects[self.rect_names[name]].rotate(theta)
        except KeyError:
            raise Error(f'There is no rectangle by the name {name}')


    

e = Physics_Canvas(15, 15, [[[1,1]], [[1,3]], [[1,1]], [[1,3]]], 1)

print(e)