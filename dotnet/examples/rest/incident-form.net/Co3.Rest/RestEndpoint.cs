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

using System;
using System.Collections.Specialized;
using System.IO;
using System.Text;
using System.Net;
using Co3.Rest.JsonConverters;

namespace Co3.Rest
{
    public abstract class RestEndpoint
    {
        public static string Co3ApiUrl { get; set; }
        protected Dto.UserSessionDto m_session;
        protected Cookie m_cookie;

        protected RestEndpoint(RestEndpoint session)
        {
            if (session != null)
            {
                m_session = session.m_session;
                m_cookie = session.m_cookie;
            }
        }

        static RestEndpoint()
        {
            Co3ApiUrl = System.Configuration.ConfigurationManager.AppSettings["Co3ApiUrl"];
        }

        public string ServerMessage { get; private set; }

        protected T HttpGet<T>(string endpointUrl)
        {
            return InvokeWebMethod<T>("GET", endpointUrl, null);
        }

        protected T HttpPost<T>(string endPointUrl, object postData)
        {
            return InvokeWebMethod<T>("POST", endPointUrl, postData);
        }

        protected T HttpPost<T>(string endPointUrl, NameValueCollection parameters, object postData)
        {
            if (parameters != null && parameters.Count > 0)
                endPointUrl += '?' + parameters.ToString();

            return InvokeWebMethod<T>("POST", endPointUrl, postData);
        }

        protected T HttpPut<T>(string endPointUrl, NameValueCollection parameters, object postData)
        {
            if (parameters != null && parameters.Count > 0)
                endPointUrl += '?' + parameters.ToString();

            return InvokeWebMethod<T>("PUT", endPointUrl, postData);
        }

        public T HttpDelete<T>(string endPointUrl)
        {
            return InvokeWebMethod<T>("DELETE", endPointUrl, null);
        }

        T InvokeWebMethod<T>(string method, string endPointUrl, object postData)
        {
            HttpWebRequest request = (HttpWebRequest)WebRequest.Create(Co3ApiUrl + endPointUrl);
            request.CookieContainer = new CookieContainer();

            request.ContentType = "application/json";
            request.Method = method;

            NameValueCollection appSettings
                = System.Configuration.ConfigurationManager.AppSettings;
            if (appSettings != null && appSettings["Co3ProxyUser"] != null)
            {
                request.Proxy.Credentials = new NetworkCredential(appSettings["Co3ProxyUser"],
                    appSettings["Co3ProxyPassword"], appSettings["Co3ProxyDomain"]);
            }
            else
                request.Credentials = CredentialCache.DefaultCredentials;

            if (m_cookie != null)
                request.CookieContainer.Add(m_cookie);

            // include session id if available
            if (m_session != null)
            {
                request.Headers.Add("X-sess-id", m_session.CsrfToken);
                request.Headers.Add("handle_format", "objects");
                request.Headers.Add("text_content_output_format", "objects_convert");
            }

            if (postData == null)
                request.ContentLength = 0;
            else
            {
                using (StreamWriter sw = new StreamWriter(request.GetRequestStream()))
                {
                    sw.Write(ToJson(postData));
                }
            }

            using (HttpWebResponse response = (HttpWebResponse)request.GetResponse())
            using (Stream data = response.GetResponseStream())
            using (StreamReader reader = new StreamReader(data))
            {
                if (response.Cookies != null
                    && response.Cookies["JSESSIONID"] != null)
                {
                    m_cookie = response.Cookies["JSESSIONID"];
                }

                return FromJson<T>(reader.ReadToEnd());
            }
        }

        public static T FromJson<T>(string json)
        {
            Newtonsoft.Json.JsonSerializerSettings settings
                = new Newtonsoft.Json.JsonSerializerSettings()
                {

                    DefaultValueHandling = Newtonsoft.Json.DefaultValueHandling.Ignore,
                    NullValueHandling = Newtonsoft.Json.NullValueHandling.Ignore
                };

            settings.Converters.Add(new UnixTimeConverter());

            try
            {
                T t = Newtonsoft.Json.JsonConvert.DeserializeObject<T>(json, settings);
                return t;
            }
            catch
            {
                throw new ArgumentException("Unable to deserialize JSON string.  Please check the JSON string is properly formatted and the object for which it represents is correct.");
            }
        }

        public static string ToJson(object obj)
        {
            StringBuilder sb = new StringBuilder();
            StringWriter sw = new StringWriter(sb);

            Newtonsoft.Json.JsonSerializer serializer = new Newtonsoft.Json.JsonSerializer()
            {
                DefaultValueHandling = Newtonsoft.Json.DefaultValueHandling.Ignore,
                NullValueHandling = Newtonsoft.Json.NullValueHandling.Ignore
            };

            serializer.Converters.Add(new UnixTimeConverter());
            serializer.Converters.Add(new Newtonsoft.Json.Converters.StringEnumConverter());
            serializer.Serialize(sw, obj);

            return sb.ToString();
        }
    }
}
