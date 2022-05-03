import numpy as np

class Physics_Canvas:
    
    def __init__(self, w, h, walls) -> None:
        self.width = w
        self.height = h
        self.matrix = self.matrix_generator(walls) #(((w0, w1), (w2, w3)...), ((h0, h1)...), ((w0, w1)...), ((h0, h1)...)) starts at top goes clockwise

    def matrix_generator(self, walls):
        matrix = np.zeros((self.height+2, self.width+2))
        slicer = {
            0 : matrix[0],
            1 : matrix[:, -1],
            2 : matrix[-1],
            3 : matrix[:, 0]
        }
        for i, e in enumerate(walls):
            print(e)
            for ee in e:
                print(ee)
                if ee != ():
                    for n in range(ee[0]+1, ee[1]+1):
                        slicer[i][n] = 1
        print(matrix)

e = Physics_Canvas(5, 5, (((0,5)), ((0,1), (3,5)), (), ()))


