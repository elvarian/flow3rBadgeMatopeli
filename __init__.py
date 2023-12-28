# flow3r imports
import struct
from st3m import InputState
from st3m.application import Application, ApplicationContext
from ctx import Context
from st3m.utils import tau
from st3m.ui.view import BaseView
from st3m.input import InputController
from st3m.ui.view import View
import random
import badgenet
import badgelink
#import machine
import socket

class Berry():
    def __init__(self):
        self.addr = ''
        
        self.berry_x = 0
        self.berry_y = 0

        self.berry_hit_radius = 7
        self.berry_shown_radius = 5

class Worm():
    def __init__(self):
        self.addr = ''

        self.line_x : int = []
        self.line_y : int = []

        self.wormLen = 100
        
        self.colorRB = random.randint(0, 255)
        self.colorGB = random.randint(0, 255)
        self.colorBB = random.randint(0, 255)

        self.colorR = self.colorRB / 255
        self.colorG = self.colorGB / 255
        self.colorB = self.colorBB / 255

        self.drawnInLobby = False

class Matopeli(BaseView):
    def __init__(self, lobby: Lobby) -> None:
        super().__init__()
        self.lobby = lobby
        self.v_x = 0.0
        self.v_y = 0.0
        self.p_x = 0.0
        self.p_y = 0.0
        
        self.berries : Berry = {}
        self.berry = Berry()
        self.berry.addr = self.lobby.addrMine
        self.berries[self.berry.addr] = self.berry

        self.worm = self.lobby.worm
        self.worms = self.lobby.worms
        
        self.printCount = 0
        self.lastPrint = 0

    def draw(self, ctx: Context) -> None:
        
        ctx.rectangle(-120, -120, 240, 240)
        ctx.rgb(0, 0, 0)
        ctx.fill()
        
        if self.berry.berry_x == 0:
            berrySet = False
            while berrySet == False:
                self.berry.berry_x = random.randint(-120, 119)
                self.berry.berry_y = random.randint(-120, 119)

                if self.berry.berry_x ** 2 + self.berry.berry_y ** 2 < 119 ** 2:
                    berrySet = True
        ctx.arc(self.berry.berry_x, self.berry.berry_y, self.berry.berry_shown_radius + 1, 0, tau, 0)
        ctx.rgb(1, 1, 1)
        ctx.fill()
        ctx.arc(self.berry.berry_x, self.berry.berry_y, self.berry.berry_shown_radius, 0, tau, 0)
        ctx.rgb(self.worm.colorR, self.worm.colorG, self.worm.colorB)
        ctx.fill()

        

        for worm in self.worms.values():
            
            if len(worm.line_x) > 0:
                #if(self.printCount < 1):
                #    print("drawing worm length: " + str(len(worm.line_x)))
                #    self.printCount += 1
                for i in range(len(worm.line_x) - 1):
                    ctx.rectangle(worm.line_x[i], worm.line_y[i], 2, 2)
                    ctx.rgb(worm.colorR, worm.colorG, worm.colorB)
                    ctx.fill()
                
                ctx.arc(worm.line_x[-1], worm.line_y[-1], 5, 0, tau, 0)
                ctx.rgb(worm.colorR, worm.colorG, worm.colorB)
                ctx.fill()

        #if self.p_x >= -120 and self.p_x < 120 and self.p_y >= -120 and self.p_y < 120:
        
        if self.p_x > self.berry.berry_x - self.berry.berry_hit_radius and self.p_x < self.berry.berry_x + self.berry.berry_hit_radius:
            if self.p_y > self.berry.berry_y - self.berry.berry_hit_radius and self.p_y < self.berry.berry_y + self.berry.berry_hit_radius:
                self.worm.wormLen += 10
                self.berry.berry_x = 0
                self.berry.berry_y = 0
                    
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
        
        self.worm.line_x.append(int(self.p_x))
        self.worm.line_y.append(int(self.p_y))

        if len(self.worm.line_x) > self.worm.wormLen:
            #i = 0
            del self.worm.line_x[0]
            del self.worm.line_y[0]

        lenX = len(self.worm.line_x)

        if lenX > 0:
            packetType = 1

            wormPacket = struct.pack('BBbb', packetType, self.worm.wormLen, self.worm.line_x[-1], self.worm.line_y[-1])
            
            #    print("[think] Sending worm packet.")

            try:
                #print("line_x: " + str(self.worm.line_x))
                #print("line_y: " + str(self.worm.line_y))
                #print("packet length: " + str(len(wormPacket)))
                #print("packet: " + bytes(wormPacket).hex())
                self.lobby.socket.sendto(wormPacket, (self.lobby.addr, 1337))
            except OSError as osError:
                exp = True    
            except Exception as e:
                
                print("[think] Catched an expection when sending worm packet: " + str(e))
                exp = True        
        msg = None
        addr = None

        try:
            msg, addr = self.lobby.socket.recvfrom(1500)
        except OSError as osError:
            exp = True
        except Exception as e:
            print("Cathced an exception while receiving packet: " + str(e))

        try:
            if msg != None and addr != None and len(msg) > 0:
                #print('[think] Received packet: ' + bytes(msg).hex())
                packetType = struct.unpack_from('B', msg, 0)

                #print('[think] Received packet: packetType: ' + str(packetType[0]) + ", packet: " + bytes(msg).hex())
                if packetType != None and len(packetType) == 1 and packetType[0] == 1:
                    
                    wormLen, line_x, line_y = struct.unpack_from('Bbb', msg, 1)
                    
                    if addr in self.worms:
                        self.worms[addr].line_x.append(line_x)
                        self.worms[addr].line_y.append(line_y)
                        self.worms[addr].wormLen = wormLen
                        if self.worms[addr].wormLen > 0:
                            while self.worms[addr].wormLen < len(self.worms[addr].line_x):
                                del self.worms[addr].line_x[0]
                                del self.worms[addr].line_y[0]
                    else:
                        worm = Worm()
                        worm.addr = addr
                        worm.line_x.append(line_x)
                        worm.line_y.append(line_y)
                        worm.wormLen = wormLen
                        self.worms[addr] = worm
                    #worm.line_x = list(line_X)
                    #worm.line_y = list(line_Y)
                    #worm.colorRB = wormR
                    #worm.colorGB = wormG
                    #worm.colorBB = wormB
                    #worm.colorR = wormR / 255
                    #worm.colorG = wormG / 255
                    #orm.colorB = wormB / 255

                    
                    #print("[think] worm addr: " + str(worm.addr))
                    #print("[think] worm colorR: " + str(worm.colorR))
                    #print("[think] worm colorG: " + str(worm.colorG))
                    #print("[think] worm colorB: " + str(worm.colorB))
                    #print("[think] worm line_x: " + str(worm.line_x))
                    #print("[think] worm line_y: " + str(worm.line_y))
                    #self.printCount += 1
                    
                    
                    
            #else:
            #    if self.lastPrint + 100 < self.ms or self.lastPrint == 0:
            #        self.lastPrint = self.ms
            #        print("[think] msg is null")
        
        except Exception as exp:
            print("Catched an exception while unpacking packet: " + str(exp))
            raise exp
            #print("Catched exception")
        #try:
        #    self.lobby.socket.sendto('MatopeliMoro', (self.lobby.addr, 1337))
        #except:
        #    exp = True

class Lobby(Application):

    def __init__(self, app_ctx: ApplicationContext) -> None:
        super().__init__(app_ctx)
        #self.input = InputController()
        #self._vm = None
        
        
        
        self.ms = 0
        
        #self.id = 0
        self.lastPrint = 0

        #print("id: " + str(self.id))

        self.ipv6addr = badgenet.get_interface().ifconfig6()[0]

        self.addr = 'ff02::1%' + badgenet.get_interface().name()
        self.addrMine = self.ipv6addr[0] + '%' + badgenet.get_interface().name()

        self.worms : Worm = {}
        self.worm = Worm()
        self.worm.addr = self.addrMine
        self.worms[self.addrMine] = self.worm
        
        self.initPacketSentCount = 0
        self.initPacketMaxSentCount = 10
        self.lastPacketSent = 0

        print('address: ' + str(self.ipv6addr))
        print('name: ' + str(badgenet.get_interface().name()))

        print('[init] Enabling left jacket...')
        badgenet.configure_jack(badgenet.SIDE_LEFT, badgenet.MODE_ENABLE_AUTO)
        self.jack = badgelink.left
        self.jack.enable()
        print('[init] Enabling right jacket...')
        badgenet.configure_jack(badgenet.SIDE_RIGHT, badgenet.MODE_ENABLE_AUTO)
        self.jack = badgelink.right
        self.jack.enable()

        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        self.socket.setblocking(False)
        self.socket.bind((self.addr, 1337))

        #if self.ipv6addr.endswith('6c:a987'):
        #if self.id == 0:
            
            
            #self.uart = machine.UART(1, baudrate=9600, tx=self.jack.ring.pin.num(), rx=self.jack.tip.pin.num())
            
            #badgelink.left.enable()
        #    print('[init] Receiving packets...')
            
            
        #elif self.ipv6addr.endswith('96:09eb'):
        #elif self.id == 1:
            
            
            #self.uart = machine.UART(1, baudrate=9600, tx=self.jack.tip.pin.num(), rx=self.jack.ring.pin.num())
            #badgenet.configure_jack(badgenet.SIDE_RIGHT, badgenet.MODE_ENABLE_AUTO)
            #self.jack = badgelink.right
            #self.jack.enable()
            #badgelink.right.enable()
        #    print('[init] Sending packets...')
            
        #else:
        #    print("[init] Could not match addres    s: " + str(self.id))

    #def on_enter(self, vm: Optional[ViewManager]) -> None:
    #    self._vm = vm
        #self.input._ignore_pressed()

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

        if len(self.worms) > 0:
            i = 0
            for worm in self.worms.values():
                #if worm.drawnInLobby == False:
                    #print("Drawing worm in lobby. " + str(worm.colorR) + ", " + str(worm.colorG) + ", " + str(worm.colorB))
                    #worm.drawnInLobby = True
                ctx.arc(-80.0 + i*50.0, 30.0, 10, 0, tau, 0)
                ctx.rgb(worm.colorR, worm.colorG, worm.colorB)
                ctx.fill()
                i += 1      

        
    
    def think(self, ins: InputState, delta_ms: int) -> None:
        super().think(ins, delta_ms) # let the input controller to its magic
        
        self.ms += delta_ms
        
        #super().think(ins, delta_ms)
        
        if self.initPacketSentCount < self.initPacketMaxSentCount or len(self.worms) < 2:
            packetType = 0

            #wormPacket = struct.pack('BBBBB' + 'b'*lenX + 'b'*lenX, packetType, self.worm.colorRB, self.worm.colorGB, self.worm.colorBB, lenX, *self.worm.line_x, *self.worm.line_y)
            wormInitPacket = struct.pack('BBBB', packetType, self.worm.colorRB, self.worm.colorGB, self.worm.colorBB)
            if self.lastPacketSent + 100 < self.ms:
                print("[think] Sending init packet")
            
                try:
                    #print("line_x: " + str(self.worm.line_x))
                    #print("line_y: " + str(self.worm.line_y))
                    #print("packet length: " + str(len(wormPacket)))
                    #print("packet: " + bytes(wormPacket).hex())
                    self.socket.sendto(wormInitPacket, (self.addr, 1337))
                    self.lastPacketSent = self.ms
                    self.initPacketSentCount += 1
                except Exception as e:
                    
                    print("[think] Catched an expection when sending worm packet: " + str(e))
                    exp = True        

        try:
            msg, addr = self.socket.recvfrom(1500)
        except OSError as osError:
            exp = True
        except Exception as e:
            print("Chatched an exception while receiving init packet: " + str(e))

        try:
            if msg != None and addr != None and len(msg) > 0:
                #print('[think] Received packet: ' + bytes(msg).hex())
                packetType = struct.unpack_from('B', msg, 0)

                print('[think] Received packet: packetType: ' + str(packetType[0]) + ", packet: " + bytes(msg).hex())
                if packetType != None and len(packetType) == 1 and packetType[0] == 0:
                    colorR, colorG, colorB = struct.unpack_from('BBB', msg, 1)
                    
                    print("[think] Got init packet: " + str(colorB) + ", " + str(colorG) + ", " + str(colorB))

                    if len(self.worms) == 0 or addr not in self.worms:
                        print("Initializing worm from addr " + str(addr))
                        worm = Worm()
                        worm.colorRB = colorR
                        worm.colorGB = colorG
                        worm.colorBB = colorB
                        worm.colorR = colorR / 255
                        worm.colorG = colorG / 255
                        worm.colorB = colorB / 255

                        self.worms[addr] = worm
                    elif len(self.worms) > 0:
                        print("worms: " + str(self.worms.values()))
                    else:
                        print("no worms in dict")
        
        except Exception as exp:
            exp = True
            #print("Catched an exception while unpacking init packet: " + str(exp))
        
        #print("Checking inputs")
        if self.input.buttons.app.right.pressed:
            print("right button pressed")
            self.vm.push(Matopeli())

        if self.input.buttons.app.left.pressed:
            print("left button pressed")
            self.vm.push(Matopeli())

        if self.input.buttons.app.middle.pressed:
            print("middle button pressed")
            self.vm.push(Matopeli(self))

#st3m.run.run_view(BaseView)