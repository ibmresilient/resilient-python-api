/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

package com.co3.activemq;

import java.net.URI;
import java.net.URISyntaxException;
import java.security.KeyStore;
import java.security.KeyStoreException;
import java.security.NoSuchAlgorithmException;
import java.security.SecureRandom;
import java.security.cert.CertificateException;
import java.security.cert.X509Certificate;
import java.util.Arrays;

import javax.net.ssl.KeyManager;
import javax.net.ssl.SSLException;
import javax.net.ssl.TrustManager;
import javax.net.ssl.TrustManagerFactory;
import javax.net.ssl.X509TrustManager;

import org.apache.activemq.ActiveMQSslConnectionFactory;

/**
 * Specialized ActiveMQ SSL/TLS connection factory that will validate
 * that the host we think we're connecting to is actually what
 * is in the certificate that the SSL/TLS server returned.
 */
public class Co3ActiveMQSslConnectionFactory extends ActiveMQSslConnectionFactory {

    public Co3ActiveMQSslConnectionFactory() {
    }
    
    public Co3ActiveMQSslConnectionFactory(String brokerURI) {
        super(brokerURI);
    }
    
    public Co3ActiveMQSslConnectionFactory(URI brokerURI) {
        super(brokerURI);
    }

    /**
     * Decorate the TrustManagers with our HostNameTrustManagerDecorator, if they
     * haven't already been decorated.
     * @param tms The TrustManagers to decorate.
     */
    private void decorateTrustManagers(TrustManager[] tms) {
        for (int i = 0; i < tms.length; i++) {
            if (tms[i] instanceof X509TrustManager
                    && !(tms[i] instanceof HostNameTrustManagerDecorator)) {
                tms[i] = new HostNameTrustManagerDecorator((X509TrustManager) tms[i]);
            }
        }
    }

    /**
     * When the super class creates the trust managers, we need to shim them with
     * our version, which will validate the host name in the certificate.
     */
    @Override
    protected TrustManager[] createTrustManager() throws Exception {
        TrustManager[] tms = super.createTrustManager();
    
        decorateTrustManagers(tms);
        
        return tms;
    }
 
    /**
     * Caller wants to set an explicit trust manager.  Make sure we've shim'd it.  Note that
     * if the caller wants to use the default (tm == null), we will have to shim the default
     * trust manager.
     */
    @Override
    public void setKeyAndTrustManagers(KeyManager[] km, TrustManager[] tm, SecureRandom random) {
        if (tm == null) {
        	// Use the default trust manager, with our decorator.
            try {
                TrustManagerFactory trustManagerFactory = TrustManagerFactory.getInstance(TrustManagerFactory.getDefaultAlgorithm());
                
                trustManagerFactory.init((KeyStore)null);
       
                TrustManager[] defManagers = trustManagerFactory.getTrustManagers();
           
                tm = Arrays.copyOf(defManagers, defManagers.length);
            
            } catch (NoSuchAlgorithmException | KeyStoreException e) {
                throw new IllegalStateException("Unable to get default trust manager", e);
            }
        }
        
        decorateTrustManagers(tm);
        
        super.setKeyAndTrustManagers(km,  tm, random);
    }
    
    /**
     * Decorator for X509TrustManager that will add support for host name
     * checking to the original.
     */
    private class HostNameTrustManagerDecorator implements X509TrustManager {
        X509TrustManager impl;
        
        HostNameTrustManagerDecorator(X509TrustManager tm) {
            this.impl = tm;
        }
        
        @Override
        public void checkClientTrusted(X509Certificate[] chain, String authType) throws CertificateException {
            impl.checkClientTrusted(chain, authType);
        }

        @Override
        public void checkServerTrusted(X509Certificate[] chain, String authType) throws CertificateException {
            impl.checkServerTrusted(chain, authType);
        
            // After the impl version was called, we can now check the host (use
            // the connection factory's URL for the host name).
            try {
                URI uri = new URI(getBrokerURL());
                String host = uri.getHost();
                
                org.apache.http.conn.ssl.SSLConnectionSocketFactory.BROWSER_COMPATIBLE_HOSTNAME_VERIFIER.verify(host, chain[0]);
            } catch (SSLException | URISyntaxException e) {
                throw new CertificateException(e.getMessage(), e);
            }
        }

        @Override
        public X509Certificate[] getAcceptedIssuers() {
            return impl.getAcceptedIssuers();
        }
    }
}
