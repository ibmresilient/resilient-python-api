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
using System.Net;
using System.Runtime.Serialization;
using Co3.Rest.JsonConverters;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest
{
    public abstract class RestEndpoint
    {
        public const string HeaderCsrfToken = "X-sess-id";
        public const string HeaderHandleFormat = "handle_format";
        public const string HeaderTextContentOutputFormat = "text_content_output_format";

        public static string Co3ApiUrl { get; set; }
        protected Dto.UserSessionDto m_session;
        private Cookie m_cookie;

        private readonly string m_proxyUser;
        private readonly string m_proxyPass;
        private readonly string m_proxyDomain;
        private readonly string m_handleFormat;
        private readonly string m_textContentOutputFormat;
        private readonly JsonSerializerSettings m_jsonSerializerSettings;

        protected RestEndpoint(RestEndpoint session)
        {
            if (session != null)
            {
                m_session = session.m_session;
                m_cookie = session.m_cookie;
            }

            NameValueCollection appSettings = System.Configuration.ConfigurationManager.AppSettings;
            m_proxyUser = appSettings["Co3ProxyUser"];
            m_proxyPass = appSettings["Co3ProxyPassword"];
            m_proxyDomain = appSettings["Co3ProxyDomain"];
            m_handleFormat = appSettings["Co3HandleFormat"];
            m_textContentOutputFormat = appSettings["Co3TextContentOutputFormat"];

            ObjectHandleFormat handleFormat;
            if (string.IsNullOrEmpty(m_handleFormat))
            {
                handleFormat = ObjectHandleFormat.Default;
                m_handleFormat = GetEnumJsonValue(handleFormat);
            }
            else
                handleFormat = (ObjectHandleFormat)Enum.Parse(typeof(ObjectHandleFormat), m_handleFormat, true);

            m_jsonSerializerSettings = new JsonSerializerSettings
            {
                DefaultValueHandling = DefaultValueHandling.Ignore,
                NullValueHandling = NullValueHandling.Ignore
            };

            m_jsonSerializerSettings.Converters.Add(new UnixTimeConverter());
            m_jsonSerializerSettings.Converters.Add(new StringEnumConverter());
            m_jsonSerializerSettings.Converters.Add(new ObjectHandleConverter(handleFormat));
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

        protected T HttpDelete<T>(string endPointUrl)
        {
            return InvokeWebMethod<T>("DELETE", endPointUrl, null);
        }

        private T InvokeWebMethod<T>(string method, string endPointUrl, object postData)
        {
            HttpWebRequest request = CreateRequest(endPointUrl);
            request.CookieContainer = new CookieContainer();

            request.ContentType = "application/json";
            request.Method = method;

            if (!string.IsNullOrEmpty(m_proxyUser))
            {
                request.Proxy.Credentials = new NetworkCredential(m_proxyUser, m_proxyPass, m_proxyDomain);
            }
            else
                request.Credentials = CredentialCache.DefaultCredentials;

            if (m_cookie != null)
                request.CookieContainer.Add(m_cookie);

            // include session id if available
            if (m_session != null)
            {
                request.Headers.Add(HeaderCsrfToken, m_session.CsrfToken);
                request.Headers.Add(HeaderHandleFormat, m_handleFormat);
                request.Headers.Add(HeaderTextContentOutputFormat, m_textContentOutputFormat);
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

            using (HttpWebResponse response = GetResponse(request))
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

        /// <summary>
        /// Method used by tests to mock the HttpWebRequest object.
        /// </summary>
        /// <param name="endpointUrl"></param>
        /// <returns></returns>
        protected virtual HttpWebRequest CreateRequest(string endpointUrl)
        {
            return (HttpWebRequest)WebRequest.Create(Co3ApiUrl + endpointUrl);
        }
        
        /// <summary>
        /// Method used by tests to verify the request
        /// </summary>
        /// <param name="request"></param>
        /// <returns></returns>
        protected virtual HttpWebResponse GetResponse(HttpWebRequest request)
        {
            return (HttpWebResponse)request.GetResponse();
        }

        private T FromJson<T>(string json)
        {
            try
            {
                return JsonConvert.DeserializeObject<T>(json, m_jsonSerializerSettings);
            }
            catch
            {
                throw new ArgumentException("Unable to deserialize JSON string. Please check the JSON string is properly formatted and the object for which it represents is correct.");
            }
        }

        protected string ToJson(object obj)
        {
            return JsonConvert.SerializeObject(obj, m_jsonSerializerSettings);
        }

        public static string GetEnumJsonValue<T>(T value)
        {
            Type type = typeof(T);
            string name = Enum.GetName(type, value);
            EnumMemberAttribute attrib = ((EnumMemberAttribute[])type.GetField(name)
                .GetCustomAttributes(typeof(EnumMemberAttribute), true))[0];
            return attrib.Value;
        }
    }
}
