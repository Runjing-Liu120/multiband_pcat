import numpy as np
import matplotlib 
import numpy as np
from astropy.io import fits
import matplotlib.pyplot as plt
from astropy.stats import sigma_clipped_stats
from image_eval import psf_poly_fit, image_model_eval

def multiband_fourier_templates(imszs, n_terms, show_templates=False):
    all_templates = []
    for b in range(len(imszs)):
        all_templates.append(make_fourier_templates(imszs[b][0], imszs[b][1], n_terms, show_templates=show_templates))
    return all_templates

def make_fourier_templates(N, M, n_terms, extradimfac=1.0, show_templates=False):
        
    templates = np.zeros((n_terms, n_terms, 4, N, M))
    
    x = np.arange(N)
    y = np.arange(M)
    
    meshx, meshy = np.meshgrid(x, y)
        
    xtemps_cos = np.zeros((n_terms, N, M))
    ytemps_cos = np.zeros((n_terms, N, M))
    
    xtemps_sin = np.zeros((n_terms, N, M))
    ytemps_sin = np.zeros((n_terms, N, M))
    
    
    for n in range(n_terms):
        xtemps_sin[n] = np.sin((n+1)*np.pi*meshx/(N*extradimfac))
        ytemps_sin[n] = np.sin((n+1)*np.pi*meshy/(M*extradimfac))
        
        xtemps_cos[n] = np.cos((n+1)*np.pi*meshx/(N*extradimfac))
        ytemps_cos[n] = np.cos((n+1)*np.pi*meshy/(M*extradimfac))
    
    for i in range(n_terms):
        for j in range(n_terms):
            templates[i,j,0,:,:] = xtemps_sin[i]*ytemps_sin[j]
            templates[i,j,1,:,:] = xtemps_sin[i]*ytemps_cos[j]
            templates[i,j,2,:,:] = xtemps_cos[i]*ytemps_sin[j]
            templates[i,j,3,:,:] = xtemps_cos[i]*ytemps_cos[j]
     
    if show_templates:
        for k in range(4):
            counter = 1
            plt.figure(figsize=(8,8))
            for i in range(n_terms):
                for j in range(n_terms):           
                    plt.subplot(n_terms, n_terms, counter)
                    plt.title('i = '+ str(i)+', j = '+str(j))
                    plt.imshow(templates[i,j,k,:,:])
                    counter +=1
            plt.tight_layout()
            plt.show()

    return templates


def generate_template(fourier_coeffs, n_terms, fourier_templates=None, N=None, M=None):
    # making n_terms explicit as an input in case we want flexibility of calling it for different numbers of terms
    if fourier_templates is None:
        fourier_templates = make_fourier_templates(N, M, n_terms)

    sum_temp = np.sum([fourier_coeffs[i,j,k]*fourier_templates[i,j,k] for i in range(n_terms) for j in range(n_terms) for k in range(4)], axis=0)
    
    return sum_temp

def fit_coeffs_to_observed_comb(observed_comb, obs_noise_sig,ftemplates, true_fcoeffs = None, true_comb=None, n_terms=None, sig_dtemp=0.1, niter=100, init_nsig=1.):
    if true_fcoeffs is not None:
        init_fcoeffs = np.random.normal(0, obs_noise_sig, size=(true_fcoeffs.shape[0], true_fcoeffs.shape[1], 4))

        n_terms = init_fcoeffs.shape[0]

    elif n_terms is not None:
        init_fcoeffs = np.random.normal(0, obs_noise_sig, size=(n_terms, n_terms, 4))

            
    running_fcoeffs = init_fcoeffs.copy()
    
    all_running_fcoeffs = np.zeros((niter//1000, n_terms, n_terms, 4))

    
    temper_schedule = np.logspace(np.log10(init_nsig), np.log10(1.), niter)
    print('temper schedule: ', temper_schedule)
    print(init_fcoeffs.shape, n_terms, ftemplates.shape)
    
    lazy_temp = generate_template(init_fcoeffs, n_terms, ftemplates)
    running_temp = lazy_temp.copy()
    lnLs = np.zeros((niter,))
    lnL = -0.5*np.sum((1./obs_noise_sig**2)*(observed_comb - running_temp)*(observed_comb-running_temp))
    lnLs[0] = lnL
    accepts= np.zeros((niter,))
    
    perts = np.random.normal(0, sig_dtemp, niter)
    
    nsamp = 0
    for n in range(niter):
        
        sig_dtemp_it = temper_schedule[n]*sig_dtemp
        
        idxk = np.random.randint(0, 4)
        idx0, idx1 = np.random.randint(0, n_terms), np.random.randint(0, n_terms)

        prop_dtemp = ftemplates[idx0,idx1,idxk,:,:]*perts[n]
        plogL = -0.5*np.sum((1./obs_noise_sig**2)*(observed_comb - running_temp - prop_dtemp)*(observed_comb-running_temp - prop_dtemp))
        
        dlogP = plogL - lnL
        
        accept_or_not = (np.log(np.random.uniform()) < dlogP)
        accepts[n] = int(accept_or_not)
        if accept_or_not:
            running_temp += prop_dtemp
            running_fcoeffs[idx0, idx1, idxk] += perts[n]
            lnLs[n] = plogL
            lnL = plogL
        else:
            lnLs[n] = lnL
        
        if n%5000==0:
            print('n = ', n)
            
        if n%1000==0:
            all_running_fcoeffs[nsamp,:,:,:] = running_fcoeffs
            nsamp += 1
            
        if n%(niter//10)==0:

            plt.figure(figsize=(16, 4))
            plt.suptitle('n = '+str(n), fontsize=20, y=1.02)
            plt.subplot(1,4,3)
            plt.title('model', fontsize=16)
            plt.imshow(running_temp)
            plt.colorbar()
            plt.subplot(1,4,2)
            plt.title('observed', fontsize=16)
            plt.imshow(observed_comb)
            plt.colorbar()
            plt.subplot(1,4,1)
            if true_comb is not None:
                plt.title('truth')
                plt.imshow(true_comb - np.mean(true_comb))
            else:
                plt.title('observed - model')
                plt.imshow(observed_comb-running_temp)
            plt.colorbar()
            plt.subplot(1,4,4)
            plt.title('$\\delta b(x,y)/\\sigma(x,y)$', fontsize=16)

            if true_comb is not None:
                resid = (observed_comb - running_temp)/obs_noise_sig
                plt.imshow(resid, vmin=np.percentile(resid, 5), vmax=np.percentile(resid, 95))
    
                plt.colorbar()
            plt.tight_layout()
            plt.show()
    
    print(np.mean(accepts))

def plot_logL(lnlz, N=100, M=100):

    plt.figure(figsize=(8, 5))
    plt.plot(np.arange(len(lnlz)), -2*lnlz, label='Chain min $\\chi_{red.}^2 = $'+str(np.round(np.min(-2*lnlz)/(N*M), 2)))
    plt.axhline(N*M, linestyle='dashed', label='$\\chi_{red.}^2 = 1$')
    plt.legend(fontsize=14)
    plt.yscale('log')
    plt.ylabel('$-2\\ln\\mathcal{L}$', fontsize=18)
    plt.xlabel('Sample iteration', fontsize=18)
    plt.tight_layout()
    plt.show() 
