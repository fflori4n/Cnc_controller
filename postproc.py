import sys

class color:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

testworkspace = True
minX = 999
minY = 999
maxX = 0
maxY = 0
Zoffset = 0 # 46
newline = ''
newcode = ''
notused = ['T1','S','M','H0','M06','G17','G20','G43','G53','G17','G21','M5','M6','M25','G49','H0','G80','G40','G49','M99']
gcode = open(sys.argv[1].strip()).read()
lines = gcode.splitlines()
with open(sys.argv[1].strip(), "w") as myfile:
		myfile.write('')
for line in lines:
	words = []
	newline = ''
	words = line.split()
	for word in words:
		if (word[0] == 'F' or word[0] == 'f') and len(word) >= 2:
			try:
				origF = int(float(word[1:]))
				word = 'F' + str(origF)
			except:
				pass
		elif (word[0] == 'Z' or word[0] == 'z') and len(word) >= 2:
			origZ = float(word[1:])
			origZ = origZ - Zoffset
			word = 'Z' + str(origZ)
			#print word
			#print origZ
		elif (word[0] == 'X' or word[0] == 'Y'):
			if(testworkspace):
				try:
					if word[0] == 'X':
						X = float(word[1:])
						if(X < minX):
							minX = x
						elif(X > maxX):
							maxX = X
					else:
						Y = float(word[1:])
						if(Y < minY):
							minY = Y
						elif(Y > maxY):
							maxY = Y
				except:
					pass
		elif ('G0' != word and 'G1' != word and 'G2' != word and 'G3' != word) and word[0] != 'X' and word[0] != 'Y':
			for cmd in notused:
				if cmd in word:
					word = ''
		newline = newline + ' ' + word
	print newline.strip()
	newline = newline.strip()
	with open(sys.argv[1].strip(), "a") as myfile:
		try:
			if(';' in newline) or newline == '\n':
				newline = ''
			else:
				myfile.write(newline.strip() + '\n')
		except:
			pass

if testworkspace:
	testgcode = 'G0 Z0\n' + 'G0 Z0\n' +'G0 X' + str(minX) + ' Y' + str(minY) + '\n' + 'G0 X' + str(maxX) + '\n' + 'G0 Y' + str(maxY) + '\n' + 'G0 X' + str(minX) + '\n' + 'G0 Y' + str(minY) + '\n'
	with open('test_gcode.ngc', "w") as myfile:
		myfile.write(testgcode)
	#newcode = newcode + '\n' + newline
#with open(sys.argv[1].strip(), "w") as text_file:
  #  text_file.write(newcode)
#print newcode

