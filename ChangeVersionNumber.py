import os,sys

def UpdateVersionNumber(releaseSignificace):
  with open("setup.py", "r") as file:

    writefile = ""
    for row in file:

      if "version" in row:
        row = row.split("=")
        versionNumber = row[1].strip().replace('"','').replace(",",'').split('.')
        if releaseSignificace == 0:
          versionNumber[1] = str(0)
          versionNumber[2] = str(0)
        elif releaseSignificace == 1:
          versionNumber[2] = str(0)

        versionNumber[releaseSignificace] = str(int(versionNumber[releaseSignificace])+1)
        row = row[0]+'='+ '"'+versionNumber[0]+'.'+versionNumber[1]+'.'+versionNumber[2]+'"'+',' + "\n"

      writefile += row
    return writefile, "v"+ versionNumber[0]+ '.' +versionNumber[1]+'.'+versionNumber[2]



def UpdateFile(newFile, version):
  #print(newFile)
  f = open("setup.py", "w", encoding="utf-8")
  f.write(newFile)
  f.close()
  print("hello there im a test text snippet!")
  #sys.stdout("hello there im a text text snippet using sys.stdout")
  return version


print(UpdateFile(UpdateVersionNumber(2)[0],UpdateVersionNumber(2)[1]))

