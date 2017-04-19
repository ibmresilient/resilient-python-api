using System;
using System.Collections.Generic;
using System.Collections.Specialized;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using Co3.Rest.Dto;
using Newtonsoft.Json;

namespace Co3.Rest.Endpoints
{
    /// <summary>
    /// Dummy class used by unit tests to access to protected members in RestEndpoint.
    /// </summary>
    public class DummyRestEndpoint : RestEndpoint
    {
        public DummyRestEndpoint(UserSessionDto session) : base(null)
        {
            m_session = session;
        }

        public T Get<T>(string endpointUrl)
        {
            return HttpGet<T>(endpointUrl);
        }

        public T Post<T>(string endPointUrl, object postData)
        {
            return HttpPost<T>(endPointUrl, postData);
        }

        public T Post<T>(string endPointUrl, NameValueCollection parameters, object postData)
        {
            return HttpPost<T>(endPointUrl, parameters, postData);
        }

        public T Put<T>(string endPointUrl, NameValueCollection parameters, object postData)
        {
            return HttpPut<T>(endPointUrl, parameters, postData);
        }

        public T Delete<T>(string endPointUrl)
        {
            return HttpDelete<T>(endPointUrl);
        }

        public string Serialize(object obj)
        {
            return ToJson(obj);
        }

        public T Deserialize<T>(string json)
        {
            return FromJson<T>(json);
        }

        public object Deserialize(string json, Type type)
        {
            return JsonConvert.DeserializeObject(json, type, m_jsonSerializerSettings);
        }
    }
}
