'''
These are constants for the unittests, each file should have specific characteristics but
the actual contents should be general enough that tests will pass
'''
#a tiff image at full size with two channels
tiffImg1 = r'F:\COMI3\160721\sc1\sc1_c1.tif'
#a sample msreg file for tiffImg1.  This is ultraflex data
tiffImg1Reg = r'F:\COMI3\160721\sc1\sc1.msreg'
#the corresponding image channel of tiffImg1
tiffImg2 = r'F:\COMI3\160721\sc1\sc1_c2.tif'
#the brightfield image ofo an ndpi file
ndpiImg1 = r'E:\COMI3\150430\islets1_Brightfield.ndpi'
#corresponding ndpi image of ndpiImg1
ndpiImg2 = r'E:\COMI3\150430\islets1_Triple.ndpi'

#an ndpi image that doesn't follow the brightfield/triple naming
singleNdpi = r'E:\COMI3\150430\islets2_bright.ndpi'
#a tiff image of channel 2 without a channel 1
tiffMissC1 = r'E:\COMI3\160414\sc1\copysc1_c2.tif'

#a image file that doesn't exist/is a jpg
failImg = r'E:\COMI3\150430\islets1_Triple.jpg'
        
#a tiff image without the decimated image pairs (8x, 64x)
noDecTif = r'F:\COMI3\160721\sc2\sc2_c1.tif'
#a tiff image with more than 2 image channels
multiTif = r'T:\Cerebellum One Left Stitched _\Cerebellum One Left Stitched __c1.tif'
#small tiff image with multiple channels.  used for quicker tests
smallTif = r'F:\COMI3\160721\sc1\small_c1.tif'
#small tiff image without multiple channels
noCTif = r'F:\COMI3\160721\sc1\small.tif'
#skip slow tests (cell find and tsp opt)
skipSlow = False