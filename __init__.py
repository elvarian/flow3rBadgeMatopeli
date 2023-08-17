# flow3r imports
from st3m import InputState
from st3m.application import Application, ApplicationContext
from ctx import Context
from st3m.utils import tau
from st3m.ui.view import BaseView
import random

class Matopeli(BaseView):
    def __init__(self) -> None:
        super().__init__()
        self.v_x = 0.0
        self.v_y = 0.0
        self.p_x = 0.0
        self.p_y = 0.0
        self.init = False
        self.snakeLen = 100

        self.line_x = []
        self.line_y = []

        self.berry_x = 0
        self.berry_y = 0
        self.berry_hit_radius = 8
        self.berry_shown_radius = 5

        self.colorR = random.randint(0, 255) / 255
        self.colorG = random.randint(0, 255) / 255
        self.colorB = random.randint(0, 255) / 255

    def draw(self, ctx: Context) -> None:
        
        ctx.rectangle(-120, -120, 240, 240)
        ctx.rgb(0, 0, 0)
        ctx.fill()
        
        if self.berry_x == 0:
            berrySet = False
            while berrySet == False:
                self.berry_x = random.randint(-120, 119)
                self.berry_y = random.randint(-120, 119)

                if self.berry_x ** 2 + self.berry_y ** 2 < 119 ** 2:
                    berrySet = True
        
        ctx.arc(self.berry_x, self.berry_y, self.berry_shown_radius, 0, tau, 0)
        ctx.rgb(self.colorR, self.colorG, self.colorB)
        ctx.fill()

        i = 0
        if len(self.line_x) > 0:
            for x in self.line_x:
                ctx.rectangle(x, self.line_y[i], 2, 2)
                
                ctx.rgb(self.colorR, self.colorG, self.colorB)
                ctx.fill()
                i += 1

        #if self.p_x >= -120 and self.p_x < 120 and self.p_y >= -120 and self.p_y < 120:
            
        ctx.arc(self.p_x, self.p_y, 5, 0, tau, 0)
        ctx.rgb(self.colorR, self.colorG, self.colorB)
        ctx.fill()

        self.line_x.append(self.p_x)
        self.line_y.append(self.p_y)

        if len(self.line_x) > self.snakeLen:
            #i = 0
            del self.line_x[0]
            del self.line_y[0]

        if self.p_x > self.berry_x - self.berry_hit_radius and self.p_x < self.berry_x + self.berry_hit_radius:
            if self.p_y > self.berry_y - self.berry_hit_radius and self.p_y < self.berry_y + self.berry_hit_radius:
                self.snakeLen += 10
                self.berry_x = 0
                self.berry_y = 0
                    
    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

        self.v_y += ins.imu.acc[0] * delta_ms / 1000.0 * 5
        self.v_x += ins.imu.acc[1] * delta_ms / 1000.0 * 5

        x = self.p_x + self.v_x * delta_ms / 1000.0
        y = self.p_y + self.v_y * delta_ms / 1000.0

        if x**2 + y**2 < (120 - 1) ** 2:
            self.p_x = x
            self.p_y = y
        else:
            self.v_x = 0
            self.v_y = 0

class Lobby(Application):

    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)

    def draw(self, ctx: Context) -> None:
        ctx.rectangle(-120, -120, 240, 240)
        ctx.rgb(0, 0, 0)
        ctx.fill()

        ctx.text_align = ctx.CENTER
        ctx.text_baseline = ctx.MIDDLE
        ctx.font_size = 30
        ctx.rgb(0.5, 0.5, 0.5)
        ctx.move_to(0, 0)
        ctx.save()
        ctx.text("LOBBY")
        ctx.restore()


    
    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms)

#st3m.run.run_view(BaseView)