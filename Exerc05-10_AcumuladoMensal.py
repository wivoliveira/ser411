# encoding: utf-8

# Nome: Willian Vieira de Oliveira      Matrícula: 139440

# Objetivo: Alterar o programa criado anteriormente para criar uma grade com o acumulado mensal para cada um dos
# seguintes sensores/satélites: {'TERRA_M-M', 'TERRA_M-T', 'AQUA_M-T', 'AQUA_M-M' }
# Dica: utilize os tipos set e dicionários!

import sys
import os
import numpy as np
try:
    from osgeo import gdal, ogr, osr
except:
    sys.exit("Erro: a biblioteca GDAL não foi encontrada!")
from utils import *

gdal.UseExceptions()
ogr.UseExceptions()
osr.UseExceptions()

vector_file = "C:/Users/Willian/Desktop/Lecture01/Queimadas/focos/focos-2016.shp"
vector_file_base_name = os.path.basename(vector_file)  # retorna "focos_2016.shp"
layer_name = os.path.splitext(vector_file_base_name)[0]  # retorna ('focos_2016','.shp') #ou seja, retorna um tupla
                                                        # (imutável, ou seja não se pode alterar, apenas visualizar)

spatial_extent = {'xmin': -89.975, 'ymin': -59.975, 'xmax': -29.975, 'ymax': 10.025}
spatial_resolution = {'x': 0.05, 'y': 0.05}
grid_dimensions = {'cols': 1200, 'rows': 1400}

file_format = "GTiff"
# Definir apenas a pasta a serem gravadas as imagens. O nome dos arquivos é definido no processamento
output_file_path = "C:/Users/Willian/Desktop/Lecture01/Queimadas/focos/"

shp_focos = ogr.Open(vector_file)
if shp_focos is None:
    sys.exit("Erro: não foi possível abrir o arquivos '{0}'".format(vector_file))

layer_focos2 = shp_focos.GetLayer(layer_name)
if layer_focos2 is None:
    sys.exit("Erro: não foi possível acessar a camada '{0}' no arquivo '{1}'!".format(layer_name, vector_file))

sensores = {'TERRA_M-M', 'TERRA_M-T', 'AQUA_M-T', 'AQUA_M-M'}
for sensor in sensores:
    for mes in range(1, 13):
        layer_focos = layer_focos2 #apenas para manter uma referência

        if mes < 9:
            query = "satelite = '%s' and timestamp > '2016/0%s' and timestamp < '2016/0%s'" % (sensor, mes, mes + 1)

        elif mes ==9:
            query = "satelite = '%s' and timestamp > '2016/0%s' and timestamp < '2016/%s'" % (sensor, mes, mes + 1)

        else:
            query = "satelite = '%s' and timestamp > '2016/%s' and timestamp < '2016/%s'" % (sensor, mes, mes + 1)

        layer_focos.SetAttributeFilter(query)
        nfocos = layer_focos.GetFeatureCount()
        print(nfocos) #query no argis resulta em 2960 para primeiro satélite e mes=1
                        # "timestamp" > '2016/01' AND "timestamp" < '2016/02' AND "satelite" ='TERRA_M-M'
                        #Resultados (TERRA_M-M): jar 2960, fev 786, mar 2023, abr 845, mai 829, jun 1510,
                        # jul 3976, ago 10797, set 12683, out 7320, nov 4836, dez 1948

        # Criando uma matriz numérica
        matriz = np.zeros((grid_dimensions['rows'], grid_dimensions['cols']), np.int16)

        # calcular o número de focos associado a cada célula
        # Itera por cada um dos focos calculando sua localização na grade:
        for foco in layer_focos:
            location = foco.GetGeometryRef()
            col, row = Geo2Grid(location, grid_dimensions, spatial_resolution, spatial_extent)
            matriz[row, col] += 1

        # criando raster de saída usando GDAL
        driver = gdal.GetDriverByName(file_format)

        if driver is None:
            sys.exit("Erro: não foi possível identificar o driver '{0}.".format(file_format))
        output_file_name = output_file_path + "Focos-" + sensor + "-" + str(mes) + ".tiff"
        raster = driver.Create(output_file_name, grid_dimensions['cols'], grid_dimensions['rows'], 1, gdal.GDT_UInt16)

        if raster is None:
            sys.exit("Erro: não foi possível criar o arquivo '{0}'.".format(output_file_name))

        # define os parâmetros de transformação de coordenadas:
        raster.SetGeoTransform(
            (spatial_extent['xmin'], spatial_resolution['x'], 0, spatial_extent['ymax'], 0, -spatial_resolution['y']))

        srs_focos = layer_focos.GetSpatialRef()
        raster.SetProjection(srs_focos.ExportToWkt())

        band = raster.GetRasterBand(1)
        band.WriteArray(matriz, 0, 0)

        band.FlushCache()
        raster = None
del raster, band
