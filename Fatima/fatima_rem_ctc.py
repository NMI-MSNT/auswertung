__author__ = 'sei'

import os

#from plotsettings import *
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
sns.set_context("paper")
sns.set_style("ticks")

import numpy as np
import scipy
import scipy.ndimage as ndimage
import scipy.ndimage.filters as filters
from skimage import exposure
from skimage import measure
from skimage.feature import peak_local_max
from skimage.filters import threshold_otsu
from skimage.io import imsave
from skimage.measure import regionprops
from skimage.morphology import reconstruction, label, disk, erosion
from skimage.morphology import remove_small_objects
from skimage.morphology import watershed
from skimage.restoration import denoise_bilateral
from skimage.segmentation import relabel_sequential, random_walker, slic
import re
import exifread
from scipy.signal import savgol_filter
import peakutils
from scipy import fftpack

nmpx = 1000/610  # nm/px


path = '/home/sei/REM/Fatima2/'
savedir = path + 'plots/'

show_plots = False

try:
    os.mkdir(savedir)
except:
    pass


files = []
for file in os.listdir(path):
    if re.search(r"\.(tif)$", file) is not None:
        files.append(file)

print(files)
do_erosion = [1,0,1,1,1]
print(do_erosion)

#file = path+files[0]

# # Open image file for reading (binary mode)
# with open(path+file, 'rb') as f:
#     tags = exifread.process_file(f)
#     for tag in tags.keys():
#         #if tag not in ('JPEGThumbnail', 'TIFFThumbnail', 'Filename', 'EXIF MakerNote'):
#         print("Key: %s, value %s" % (tag, tags[tag]))


coverage = np.array([])
n = np.array([])
area_mean = np.array([])
area_err = np.array([])

labels = np.array([])

ctc = []
radii = []

for f,file in enumerate(files):
    print(file)
    labels = np.append(labels, file[:-4])
    file = path+file

    pic = scipy.misc.imread(file)
    #print("Image Size: " + str(pic.shape))
    pic = pic[:1780,:]
    pic = exposure.rescale_intensity(pic)

    ffile = file[:-4] + '_denoised.jpg'
    if os.path.isfile(ffile):
        pic = scipy.misc.imread(ffile)
    else:
        pic = denoise_bilateral(pic, sigma_color=0.1, sigma_spatial=3, multichannel=False)
        #pic = denoise_bilateral(pic, sigma_color=0.01, sigma_spatial=1, multichannel=False)
        scipy.misc.imsave(ffile, pic)


    #p1, p99 = np.percentile(pic, (1, 99))
    #pic = exposure.rescale_intensity(pic, in_range=(p1, p99))

    if do_erosion[f]:
        pic = erosion(pic, disk(5))
        pic = erosion(pic, disk(3))
        pic = erosion(pic, disk(1))

    thresh = threshold_otsu(pic)*1.0

    mask = pic
    h = thresh
    seed = pic - h
    dilated = reconstruction(seed, mask, method='dilation')
    pic = pic - dilated

    if show_plots:
        plt.imshow(pic)
        plt.show()

    thresh = threshold_otsu(pic)
    bin = pic > thresh
    #bin = pic > np.max(pic)/2

    if show_plots:
        plt.imshow(bin)
        plt.show()


    all_labels = measure.label(bin)
    blobs_labels = measure.label(bin, background=0)

    rs = np.zeros(0)
    for region in regionprops(blobs_labels):
        rs = np.hstack((rs, region.equivalent_diameter*nmppx(mags[f])))

    mask = (rs > 10) & (rs < 120)
    rs = rs[mask]
    #n_hist, b, patches = plt.hist(rs.ravel(), 100, histtype='stepfilled')
    #plt.show()
    n_hist, bin_edges = np.histogram(rs.ravel(), bins=100,density=True)
    x = bin_edges[:-1]
    y = n_hist
    mask = (y > 0)
    x = x[mask]
    y = y[mask]
    filtered = savgol_filter(y, 11, 2)
    filtered = savgol_filter(filtered, 11, 2)
    indexes = peakutils.indexes(filtered, thres=2e-5, min_dist=10)
    sorted = np.flipud(np.argsort(y[indexes]))
    indexes = indexes[sorted]
    # print(indexes)
    # print(x[indexes[0]])
    # plt.scatter(x,y)
    # plt.plot(x,filtered)
    # plt.text(x[indexes[0]], filtered[indexes[0]], str(int(round(x[indexes[0]]))), zorder=10)
    # plt.show()
    radii.append(x[indexes[0]])

    xy = np.array([0,2])
    for region in regionprops(blobs_labels):
        xy = np.vstack((xy, region.centroid))

    print(xy.shape)

    dists = np.zeros((xy.shape[0],xy.shape[0]))
    for i in range(xy.shape[0]):
        for j in range(xy.shape[0]):
            #if i != j:
                dists[i,j] = np.sqrt( (xy[i,0]-xy[j,0])**2 + (xy[i,1]-xy[j,1])**2 )*nmpx

    #n_hist, b, patches = plt.hist(dists.ravel(), 1000, histtype='stepfilled')
    n_hist, bin_edges = np.histogram(dists.ravel(), bins=1000,density=True)
    x = bin_edges[:-1]
    y = n_hist

    filtered = savgol_filter(y, 11, 2)
    filtered = savgol_filter(filtered, 11, 2)

    #plt.xlim((60,1000))
    mask = (x > 60) & (x < 1000)
    x = x[mask]
    y = y[mask]
    filtered = filtered[mask]

    indexes = peakutils.indexes(filtered, thres=2e-5, min_dist=10)
    indexes = indexes[0:7]
    if show_plots:
        for m, ind in enumerate(indexes):
            plt.text(x[ind], filtered[ind], str(int(round(x[ind]))), zorder=10)

        plt.plot(x,y)
        plt.plot(x,filtered)
        plt.title(file)
        plt.show()

    d = x[indexes]
    print(d)
    ctc.append(d[0])



print(ctc)

f = open(path + "ctc.txt", 'w')
f.write("file,ctc"+"\r\n")
for i in range(len(ctc)):
    f.write(files[i] + ','+str(ctc[i]))
    f.write("\r\n")

f.close()


print(radii)

f = open(path + "radii.txt", 'w')
f.write("file,radius"+"\r\n")
for i in range(len(radii)):
    f.write(files[i] + ','+str(radii[i]))
    f.write("\r\n")

f.close()




# for array in arrays:
#
#     print('-> Starting with ' + sample + ' ' + array)
#
#     savedir = path + array + '/plots/'
#     fname = path + array + '/' + sample + "_" + array + ".jpg"
#     # fname = path + "test.png"
#
#
#     show_plots = False
#
#
#     def plot_particles(image1, image2, image3, fname):
#         fig, axes = plt.subplots(ncols=3, figsize=(8, 2.7))
#         ax0, ax1, ax2 = axes
#         ax0.imshow(image1, interpolation='nearest')
#         # ax0.set_title('Overlapping objects')
#         ax1.imshow(image2, cmap=plt.cm.jet, interpolation='nearest')
#         # ax1.set_title('Distances')
#         ax2.imshow(image3, cmap=plt.cm.spectral, interpolation='nearest')
#         # ax2.set_title('Separated objects')
#         for ax in axes:
#             ax.axis('off')
#         fig.subplots_adjust(hspace=0.01, wspace=0.01, top=1, bottom=0, left=0, right=1)
#         # plt.show()
#         plt.savefig(fname)
#         plt.close()
#
#
#     def plot_comparison(original, filtered):
#         fig, (ax1, ax2) = plt.subplots(ncols=2, figsize=(8, 4))
#         ax1.imshow(original)
#         ax1.axis('off')
#         ax2.imshow(filtered)
#         ax2.axis('off')
#
#
#     try:
#         os.mkdir(path + savedir)
#     except:
#         pass
#
#     print("-> loading and processing sem image")
#
#     data = scipy.misc.imread(fname)
#     print("Image Size: " + str(data.shape))
#     # data = data[:,:,0]
#     data = exposure.rescale_intensity(data)
#
#     sname = fname[:-4] + '_denoised.jpg'
#     if os.path.isfile(sname):
#         fdata = scipy.misc.imread(sname)
#     else:
#         #fdata = denoise_bilateral(data, sigma_color=0.1, sigma_spatial=3, multichannel=False)
#         fdata = denoise_bilateral(data, sigma_color=0.01, sigma_spatial=1, multichannel=False)
#         scipy.misc.imsave(sname, fdata)
#
#     oname = fname[:-4] + '_opt.jpg'
#     if os.path.isfile(oname):
#         fdata = scipy.misc.imread(oname)
#     else:
#         # p1, p99 = np.percentile(data, (1, 99))
#         # data = exposure.rescale_intensity(data, in_range=(np.min(data)*100, np.max(data)*100))
#         seed = np.copy(fdata)
#         seed[1:-1, 1:-1] = fdata.min()
#         fdata = fdata - reconstruction(seed, fdata, method='dilation')
#         fdata = filters.gaussian_filter(fdata, sigma=5)
#         seed = None
#
#         seed = np.copy(fdata)
#         seed[1:-1, 1:-1] = fdata.min()
#         fdata = fdata - reconstruction(seed, fdata, method='dilation')
#         seed = None
#         scipy.misc.imsave(oname, fdata)
#
#     data = np.flipud(data)
#     fdata = np.flipud(fdata)
#
#     if show_plots:
#         plt.imshow(fdata, cmap="gray")
#         plt.show()
#
#     thresh = threshold_otsu(fdata)
#     bin = fdata > thresh
#
#     print("-> searching blobs")
#
#     labeled, n = ndimage.label(bin)
#     # labeled = remove_small_objects(labeled, 400)
#
#     # plt.imshow(labeled)
#     # plt.savefig(savedir+"blobdetect.png")
#     # plt.close()
#
#     # xy = np.array(ndimage.center_of_mass(fdata, labeled, range(1, n + 1)))
#     # xy = xy[:,[1,0]]
#
#     xy = np.zeros((0, 2))
#     for region in regionprops(labeled):
#         if region.area > 400:
#             xy = np.vstack((xy, region.centroid))
#
#     xy = xy[:, [1, 0]]
#
#     if show_plots:
#         plt.imshow(labeled)
#         plt.plot(xy[:, 0], xy[:, 1], "rx")
#         plt.show()
#
#     x = []
#     y = []
#     low_dist = False
#     low_ind = -1
#     for i in range(xy.shape[0]):
#         if xy[i, 0] > 0:
#             for j in range(xy.shape[0]):
#                 if (i != j):
#                     d = np.sqrt((xy[i, 0] - xy[j, 0]) ** 2 + (xy[i, 1] - xy[j, 1]) ** 2)
#                     if d < 150:
#                         low_dist = True
#                         low_ind = j
#             if low_dist:
#                 x = np.append(x, xy[i, 0] - (xy[i, 0] - xy[low_ind, 0]) / 2)
#                 y = np.append(y, xy[i, 1] - (xy[i, 1] - xy[low_ind, 1]) / 2)
#                 xy[low_ind, :] = 0
#                 low_dist = False
#             else:
#                 x = np.append(x, xy[i, 0])
#                 y = np.append(y, xy[i, 1])
#
#     xy = np.transpose(np.array([x, y]))
#     print(str(len(xy)) + ' valid blobs found')
#
#     print("-> fitting grid")
#     inds, nxy, ids = fit_grid(xy, nx, ny)
#
#     print(nxy.shape)
#
#     n = nxy.shape[0]
#
#     print("-> plotting "+str(n)+" individual structures")
#     try:
#         os.mkdir(savedir)
#     except:
#         pass
#     particles = np.zeros(n)
#     area = np.zeros(n)
#     dist = np.zeros(n)
#     rdiff = np.zeros(n)
#     width = 80
#
#     for i in range(n):
#         x = nxy[i, 0]
#         y = nxy[i, 1]
#         x = int(x)
#         y = int(y)
#         if x - width > 0:
#             xstart = x - width
#         else:
#             xstart = 0
#
#         if x + width < data.shape[1] - 1:
#             xstop = x + width
#         else:
#             xstop = data.shape[1] - 1
#
#         if y - width > 0:
#             ystart = y - width
#         else:
#             ystart = 0
#
#         if y + width < data.shape[0] - 1:
#             ystop = y + width
#         else:
#             ystop = data.shape[0] - 1
#
#         sub = data[ystart:ystop, xstart:xstop]
#         #sub2 = data[ystart:ystop, xstart:xstop]
#         sub = denoise_bilateral(sub, sigma_color=0.1, sigma_spatial=15, multichannel=False)
#
#         buf = np.zeros((2 * width, 2 * width))
#         buf[:sub.shape[0], :sub.shape[1]] = sub
#
#         thresh = threshold_otsu(sub) * 1.15
#         bin = sub > thresh
#         # area[i] = np.sum(bin)
#
#         labeled, n = ndimage.label(bin)
#
#         thresh = threshold_otsu(sub) * 1.3
#         bin = sub > thresh
#         # bin = convex_hull_image(bin)
#         bin = ndimage.binary_fill_holes(bin)
#         sub = buf
#         sub = np.flipud(sub)
#
#         p2, p98 = np.percentile(sub, (2, 100))
#         sub = exposure.rescale_intensity(sub, in_range=(p2, p98))
#         # labeled, n = ndimage.label(bin)
#         distance = ndimage.distance_transform_edt(bin)
#         distance = filters.gaussian_filter(distance, sigma=5)
#         local_maxi = peak_local_max(distance, indices=False, footprint=np.ones((3, 3)), labels=bin)
#         markers = measure.label(local_maxi)
#         labeled = watershed(-distance, markers, mask=bin)
#         # markers[~bin] = -1
#         # labeled = segmentation.random_walker(bin,markers)
#         labeled = remove_small_objects(labeled, 100)
#         labeled = relabel_sequential(labeled)[0]
#
#         xy = np.zeros((0, 2))
#         areas = np.zeros((0, 1))
#         for region in regionprops(labeled):
#             if region.area > 100:
#                 area[i] += region.area
#                 xy = np.vstack((xy, region.centroid))
#                 areas = np.vstack((areas, region.area*nmpx**2))
#
#         num = xy.shape[0]
#
#         imsave(savedir + ids[i] + ".png", sub)
#
#         particles[i] = num
#
#         if num == 2:
#             if areas[0] > areas[1]:
#                 r1 = np.sqrt(areas[0]/np.pi)
#                 r2 = np.sqrt(areas[1]/np.pi)
#             else:
#                 r1 = np.sqrt(areas[1]/np.pi)
#                 r2 = np.sqrt(areas[0]/np.pi)
#
#             rdiff[i] = (r1 - r2) / r1
#
#             c1 = measure.find_contours(labeled == 2, 0)[0]
#             c2 = measure.find_contours(labeled == 1, 0)[0]
#
#             plt.plot(c1[:, 0], c1[:, 1])
#             plt.plot(c2[:, 0], c2[:, 1])
#             plt.savefig(savedir + ids[i] + "_contour.pdf")
#             plt.close()
#
#             d = np.array([])
#             for k in range(c1.shape[0]):
#                 for l in range(c2.shape[0]):
#                     d = np.append(d, np.sqrt(
#                         np.power(np.real(c1[k, 0] - c2[l, 0]), 2) + np.power(np.real(c1[k, 1] - c2[l, 1]), 2)))
#             dist[i] = np.min(d) * nmpx
#             print('structure ' + ids[i] + ' has 2 blobs with a gap of: ' + str(dist[i]) + ' nm')
#         else:
#             rdiff[i] = -1.0
#             dist[i] = -1.0
#             print('structure ' + ids[i] + ' has ' + str(num) + ' blobs')
#
#         # particles[i] = area[i] /
#         plot_particles(sub, distance, labeled, savedir + ids[i] + "_detection.pdf")
#
#     # sorted = np.argsort(area)
#     # area = area[sorted]
#     # particles = particles[sorted]
#
#     ids = np.array(ids)
#
#     # ids = ids[sorted]
#     # data = np.append(ids.reshape(ids.shape[0], 1), area.reshape(area.shape[0], 1),1)
#     # data = np.append(data,particles.reshape(particles.shape[0], 1), 1)
#
#     print('-> Writing measured values to file')
#     f = open(path + array + "/" + sample + "_" + array + "_particles_SEM.csv", 'w')
#     f.write("id,area,rdiff,dist,particles" + "\r\n")
#     for i in range(len(ids)):
#         f.write(str(ids[i]) + "," + str(area[i]) + "," + str(rdiff[i]) + "," + str(dist[i]) + "," + str(particles[i]) + "\r\n")
#
#     f.close()
#
#     data = None
#     fdata = None
#     print('-> Processing of ' + array + ' finished')
