'''Noesis import plugin. Written by Tsukihime'''

from inc_noesis import *
import noesis
import rapi

def registerNoesisTypes():
    '''Register the plugin. Just change the Game name and extension.'''

    handle = noesis.register("Music Girl for Miku", ".mdl")
    noesis.setHandlerTypeCheck(handle, noepyCheckType)
    noesis.setHandlerLoadModel(handle, noepyLoadModel)
    return 1

def noepyCheckType(data):
    '''Verify that the format is supported by this plugin. Default yes'''

    bs = NoeBitStream(data)
    idstring = noeStrFromBytes(bs.readBytes(4))
    if idstring == "mdl ":
        return 1
    return 0

def noepyLoadModel(data, mdlList):
    '''Build the model, set materials, bones, and animations. You do not
    need all of them as long as they are empty lists (they are by default)'''

    ctx = rapi.rpgCreateContext()
    parser = SanaeParser(data)
    parser.parse_file()
    mdl = rapi.rpgConstructModel()
    mdl.setModelMaterials(NoeModelMaterials(parser.texList, parser.matList))
    mdl.setBones(parser.boneList)
    mdl.setAnims(parser.animList)
    mdlList.append(mdl)
    return 1

class Mesh(object):

    def __init__(self):

        self.name = ""
        self.numVerts = 0
        self.vertSize = 0
        self.vertBuff = bytes()
        self.vertOfs = -1
        self.weightOfs = -1
        self.parts = []

class MeshPart:
    def __init__(self, numIdx, matNum, idxBuff):
        self.numIdx = numIdx
        self.matNum = matNum
        self.idxBuff = idxBuff

class SanaeParser(object):

    def __init__(self, data):
        '''Initialize some data. Refer to Sanae.py to see what is already
        initialized'''

        self.inFile = NoeBitStream(data)
        self.animList = []
        self.texList = []
        self.matList = []
        self.boneList = []
        self.meshList = []

    def build_meshes(self):

        for mesh in self.meshList:
            for part in mesh.parts:
                rapi.rpgBindPositionBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 0)
                rapi.rpgBindNormalBufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 12)
                rapi.rpgBindUV1BufferOfs(mesh.vertBuff, noesis.RPGEODATA_FLOAT, 32, 24)
                matName = self.matList[part.matNum].name
                rapi.rpgSetMaterial(matName)
                rapi.rpgCommitTriangles(part.idxBuff, noesis.RPGEODATA_USHORT, part.numIdx, noesis.RPGEO_TRIANGLE_STRIP, 1)

    def read_name(self):

        #string = self.inFile.readBytes(n)
        return noeStrFromBytes(string)

    def parse_materials(self, numMat):

        for i in range(numMat):
            self.inFile.read('8f')
            texNum = self.inFile.readUInt()
            self.inFile.read('6f')
            self.inFile.readUInt()

            # texName = self.texList[texNum].name
            # material = NoeMaterial("material_%d" %i, texName)
            matName = self.texList[texNum].name
            texName = matName
            material = NoeMaterial(matName, texName)
            self.matList.append(material)


    def load_texture(self, texData, texName):

        pvr = PVRTCImage(NoeBitStream(texData))
        pvr.parseImageInfo()
        tex = NoeTexture("pvrtex", pvr.w/8, pvr.h/8, pvr.decode(), noesis.NOESISTEX_RGBA32)
        tex.name = texName
        self.texList.append(tex)

    def parse_textures(self, numTex):
        for i in range(numTex):
            offset, size, unk1, unk2 = self.inFile.read('4I')
            curr = self.inFile.tell()
            self.inFile.seek(offset)
            texData = self.inFile.readBytes(size)
            texName = "texture_%d" %i
            #tex = rapi.loadTexByHandler(texData, "pvr")
            #if tex:
                #tex.name = texName
                #self.texList.append(tex)

            f = open('data/' + texName + '.pvr', 'wb')
            f.write(texData)
            f.close()

            self.load_texture(texData, texName)
            self.inFile.seek(curr)

    def parse_vertices(self, numVerts):

        return self.inFile.readBytes(numVerts * 32)

    def parse_faces(self, numIdx):

        return self.inFile.readBytes(numIdx * 2)

    def parse_mesh_info(self, count):

        for i in range(count):
            mesh = Mesh()
            mesh.numParts = self.inFile.readUInt()
            mesh.numVerts = self.inFile.readUInt()
            self.inFile.seek(72, 1)

            self.meshList.append(mesh)

    def parse_meshes(self, numMesh):

        for i in range(numMesh):
            mesh = self.meshList[i]
            self.inFile.seek(mesh.vertOfs)
            mesh.vertBuff = self.parse_vertices(mesh.numVerts)

            self.inFile.seek(mesh.idxOfs)
            for j in range(mesh.numParts):
                numIdx, matNum = self.inFile.read('2H')
                idxBuff = self.parse_faces(numIdx)
                part = MeshPart(numIdx, matNum, idxBuff)
                mesh.parts.append(part)

    def parse_file(self):
        '''Main parser method'''

        idstring = self.inFile.readBytes(4)
        unk1, unk2, unk3, numMesh = self.inFile.read('4I')
        self.inFile.readInt()
        self.inFile.seek(72, 1)

        self.parse_mesh_info(numMesh)

        numBones, boneOfs, unk, unk = self.inFile.read('4I')
        numMat, matOfs, unk, unk = self.inFile.read('4I')
        numTex, texOfs, unk, unk = self.inFile.read('4I')

        for i in range(numMesh):
            self.meshList[i].vertOfs = self.inFile.readUInt()

        for i in range(numMesh):
            self.meshList[i].idxOfs = self.inFile.readUInt()

        for i in range(numMesh):
            self.meshList[i].weightOfs = self.inFile.readUInt()

        self.parse_textures(numTex)

        self.parse_meshes(numMesh)

        self.inFile.seek(matOfs)
        self.parse_materials(numMat)

        self.build_meshes()

class PVRTCImage:
    def __init__(self, reader):
        self.reader = reader

    def parseV2(self):
        self.reader.seek(4, NOESEEK_ABS)
        self.w = self.reader.readInt()
        self.h = self.reader.readInt()
        self.mipMapCount = self.reader.readInt() + 1
        self.flags = self.reader.readInt()
        self.dataSize = self.reader.readInt()
        self.bpp = self.reader.readInt()
        self.redMask = self.reader.readInt()
        self.greenMask = self.reader.readInt()
        self.blueMask = self.reader.readInt()
        self.alphaMask = self.reader.readInt()
        self.pvrIdentifier = self.reader.readUInt()
        self.numSourfaces = self.reader.readInt() + 1
        if self.pvrIdentifier != 0x21525650: #"PVR!"
            return 0
        if self.flags & 0x10000:
            self.flip = 1
        self.dataOfs = 52
        return 1

    def parseV3(self):
        if self.reader.getSize() < 68:
            return 0
        self.reader.seek(4, NOESEEK_ABS)
        self.asz = self.reader.readInt()
        self.fmt = self.reader.readInt()
        if self.fmt == 1:
            self.bpp = 2
        elif self.fmt == 3:
            self.bpp = 4
        else:
            return 0
        self.reader.seek(24, NOESEEK_ABS)
        self.w = self.reader.readInt()
        self.h = self.reader.readInt()
        self.reader.seek(48, NOESEEK_ABS)
        self.metaLen = self.reader.readInt()
        if self.metaLen > 4:
            if self.reader.readInt() == 0x3525650:
                self.flip = 1
        self.dataOfs = 52+self.metaLen
        return 1

    def parseImageInfo(self):
        if self.reader.getSize() < 52:
            return 0

        self.flip = 0
        self.ver = self.reader.readInt()
        if self.ver == 52:
            return self.parseV2()
        elif self.ver == 0x3525650:
            return self.parseV3()

        return 0

    def decode(self):

        self.reader.seek(self.dataOfs, NOESEEK_ABS)
        d = 4 if self.bpp == 2 else 2
        encodedData = self.reader.readBytes((self.w*self.h) // d)
        r = rapi.imageDecodePVRTC(encodedData, self.w, self.h, -self.bpp)
        if self.flip == 1:
            r = rapi.imageFlipRGBA32(r, self.w, self.h, 0, 1)
        return r
