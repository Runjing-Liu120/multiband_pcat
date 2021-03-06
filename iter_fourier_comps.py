from pcat_spire import *


''' this script is for testing the iterative background estimation suggested by Mike. the main idea is to 
gradually reduce the minimum flux threshold of the cataloger while fitting fourier coefficients to observations at 
250 micron. as Fmin gets reduced, the fourier coefficients shift as they do not need to model previously sub-Fmin sources.
After a few iterations, the best fit template is saved and used to model the background of all three bands. once the multiband fitting begins, 
the colors of the background model are fixed and so are its fourier coefficients.'''

base_path = '/Users/luminatech/Documents/multiband_pcat/'
result_path = '/Users/luminatech/Documents/multiband_pcat/spire_results/'

initial_template_amplitude_dicts = dict({'sze': dict({'S':0.00, 'M':0.002, 'L':0.01}), 'planck': dict({'S':1.0, 'M':1.0, 'L':1.0})})

t_filenames = ['Data/spire/rxj1347/rxj1347_PSW_nr_sze.fits']

template_names = ['sze']

cluster_name='rxj1347'


n_fc_terms = 8

init_fc = np.zeros(shape=(n_fc_terms, n_fc_terms, 4))

fmin_levels = [0.05, 0.02, 0.01, 0.005]

nsamps = [50, 100, 200, 500]

median_fcs_iter = []

timestr = None

for i, fmin in enumerate(fmin_levels):
	if i==0:
		print('initial fourier coefficients set to zero')
		median_fc = init_fc

	ob = lion(band0=0, base_path=base_path, result_path=result_path, round_up_or_down='down', bolocam_mask=True, float_background=True, burn_in_frac=0.75, bkg_sig_fac=5.0, bkg_sample_delay=0,\
		 cblas=True, openblas=False, visual=True, show_input_maps=False, float_templates=False, tail_name=cluster_name+'_PSW_nr_1_ext',\
		  dataname='rxj1347_831', bias=[-0.004], load_state_timestr=timestr, max_nsrc=1000, auto_resize=True, trueminf=fmin, nregion=5, weighted_residual=True,\
		   make_post_plots=False, nsamp=nsamps[i], use_mask=True, residual_samples=5, init_fourier_coeffs=median_fc, n_frames=3, float_fourier_comps=True, n_fourier_terms=n_fc_terms,\
		    show_fc_temps=False, fc_sample_delay=0, fourier_comp_moveweight=40., alph=1.0, dfc_prob=1.0)

	# ob = lion(band0=0, base_path=base_path, result_path=result_path, round_up_or_down='down', bolocam_mask=False, float_background=True, burn_in_frac=0.75, bkg_sig_fac=5.0, bkg_sample_delay=0,\
	# 	 cblas=True, openblas=False, visual=True, show_input_maps=False, float_templates=False, tail_name='as0592_PSW_nr_1_ext',\
	# 	  dataname='as0592_925', bias=[-0.004], load_state_timestr=timestr, max_nsrc=1000, auto_resize=True, trueminf=fmin, nregion=5, weighted_residual=True,\
	# 	   make_post_plots=False, nsamp=nsamps[i], use_mask=True, residual_samples=20, init_fourier_coeffs=median_fc, n_frames=3, float_fourier_comps=True, n_fourier_terms=n_fc_terms,\
	# 	    show_fc_temps=False, fc_sample_delay=0, fourier_comp_moveweight=40., alph=1.0)

	# ob = lion(band0=0, base_path=base_path, result_path=result_path, round_up_or_down='down', bolocam_mask=True, float_background=True, burn_in_frac=0.75, bkg_sig_fac=5.0, bkg_sample_delay=0, \
	# 		 cblas=True, openblas=False, visual=True, show_input_maps=False, float_templates=False, tail_name='rxj1347_PSW_nr_1_ext',\
	# 		  dataname='rxj1347_831', bias=[-0.004], load_state_timestr=timestr,  max_nsrc=600, auto_resize=True, trueminf=fmin, nregion=5, weighted_residual=True,\
	# 		  nsamp=nsamps[i], use_mask=True, make_post_plots=False, residual_samples=20, init_fourier_coeffs=median_fc, n_frames=3, float_fourier_comps=True, n_fourier_terms=n_fc_terms, fc_sample_delay=0, fourier_comp_moveweight=40.)

	print(ob.gdat.imsz0[0])
	ob.main()
	_, filepath, _ = load_param_dict(ob.gdat.timestr)
	timestr = ob.gdat.timestr

	chain = np.load(filepath+'/chain.npz')
	median_fc = np.median(chain['fourier_coeffs'][-10:], axis=0)

	# print('median_fc has shape ', median_fc.shape)
	# print(median_fc)
	median_fcs_iter.append(median_fc)
	median_fc_temp = generate_template(median_fc, n_fc_terms, N=ob.gdat.imsz0[0], M=ob.gdat.imsz0[1])

	plt.figure()
	plt.imshow(median_fc_temp, cmap='Greys', interpolation=None, origin='lower')
	plt.colorbar()
	plt.savefig('median_fc_temp_iter'+str(i)+'_10_13_20_nfcterms='+str(n_fc_terms)+'_'+cluster_name+'.png', bbox_inches='tight')

	# plt.savefig('median_fc_temp_iter'+str(i)+'_10_13_20_nfcterms='+str(n_fc_terms)+'_as0592.png', bbox_inches='tight')
	plt.close()



# print('median_fc issss')
# print(median_fc)
final_temp = generate_template(median_fc, n_fc_terms, N=ob.gdat.imsz0[0], M=ob.gdat.imsz0[1])
plt.figure()
plt.imshow(final_temp, cmap='Greys', interpolation=None, origin='lower')
plt.colorbar()
plt.savefig('final_fc_temp_iter'+'_10_13_20_nfcterms='+str(n_fc_terms)+'_'+cluster_name+'.png', bbox_inches='tight')
# plt.savefig('final_fc_temp_iter'+'_10_13_20_nfcterms='+str(n_fc_terms)+'_as0592.png', bbox_inches='tight')
plt.close()
# plt.show()

np.savez('median_fc_iter'+'_10_13_20_nfcterms='+str(n_fc_terms)+'_'+cluster_name+'.npz', median_fcs_iter=median_fcs_iter)

initial_template_amplitude_dicts = dict({'sze': dict({'S':0.00, 'M':0.000, 'L':0.014})})

template_names = ['sze']


ob = lion(band0=0, band1=1, band2=2, base_path=base_path, result_path=result_path, round_up_or_down='down', bolocam_mask=True, float_background=True, burn_in_frac=0.75, bkg_sig_fac=5.0, bkg_sample_delay=0, temp_sample_delay=50,\
		 cblas=True, openblas=False, visual=True, show_input_maps=False, float_templates=True, template_names=template_names, init_template_amplitude_dicts=initial_template_amplitude_dicts, tail_name='rxj1347_PSW_nr_1_ext',\
		  dataname='rxj1347_831', bias=[-0.004, -0.007, -0.008], delta_cp_bool=True, max_nsrc=1000, init_fourier_coeffs=median_fc, auto_resize=True, trueminf=0.005, nregion=5, weighted_residual=True,\
		   make_post_plots=True, nsamp=2000, use_mask=True, residual_samples=200, template_filename=None, float_fourier_comps=True, show_fc_temps=False, n_fourier_terms=n_fc_terms, fc_sample_delay=0, fourier_comp_moveweight=0., \
		   movestar_sample_delay=0, merge_split_sample_delay=0, birth_death_sample_delay=0, n_frames=20, alph=1.0, dfc_prob=0.0, fc_rel_amps=[1.0, 0.5, 0.25])

ob.main()

# ob = lion(band0=0, base_path=base_path, result_path=result_path, round_up_or_down='down', bolocam_mask=False, float_background=True, burn_in_frac=0.75, bkg_sig_fac=5.0, bkg_sample_delay=0,\
# 	 cblas=True, openblas=False, visual=True, show_input_maps=False, float_templates=False, tail_name=cluster_name+'_PSW_nr_1_ext',\
# 	  dataname='rxj1347_831', bias=[-0.004], load_state_timestr=timestr, max_nsrc=1000, auto_resize=True, trueminf=fmin, nregion=5, weighted_residual=True,\
# 	   make_post_plots=False, nsamp=nsamps[i], use_mask=True, residual_samples=20, init_fourier_coeffs=median_fc, n_frames=3, float_fourier_comps=True, n_fourier_terms=n_fc_terms,\
# 	    show_fc_temps=False, fc_sample_delay=0, fourier_comp_moveweight=40., alph=1.0)
# np.savez('median_fc_iter'+'_10_13_20_nfcterms='+str(n_fc_terms)+'_as0592.npz', median_fcs_iter=median_fcs_iter)


