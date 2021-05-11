#def beep():
#    print "\a"
#beep()



import os

duration = 0.15  # seconds
duration2 = duration*2  # seconds
duration3 = duration*3  # seconds
sol1 = 49  # Hz
la4 = 440  # Hz
si4 = 493.88  # Hz
do = 523.25  # Hz
re = 587.33  # Hz
mi = 659.25  # Hz
fa = 698.46  # Hz
sol = 783.99  # Hz
la = 880  # Hz
laB = 830.61  # Hz
miB = 622.25  # Hz

si = 987.77  # Hz
do6 = 1046.50  # Hz

def finished() :
    os.system('play -nq -t alsa synth {} sine {}'.format(duration3, do))
    os.system('play -nq -t alsa synth {} sine {}'.format(duration3, sol))
    os.system('play -nq -t alsa synth {} sine {}'.format(duration2, laB))
    os.system('play -nq -t alsa synth {} sine {}'.format(duration, miB))
    #os.system('play -nq -t alsa synth {} sine {}'.format(duration, sol1))
    #os.system('play -nq -t alsa synth {} sine {}'.format(duration, sol))
    #os.system('play -nq -t alsa synth {} sine {}'.format(duration3, do6))

finished()

