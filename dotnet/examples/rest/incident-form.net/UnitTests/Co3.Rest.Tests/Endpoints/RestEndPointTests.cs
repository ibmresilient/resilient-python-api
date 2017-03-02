using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using Co3.Rest.Dto;
using Co3.Rest.Endpoints;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Moq;
using Moq.Protected;
using Newtonsoft.Json;

namespace Co3.Rest.EndPoints
{
    [TestClass]
    public class RestEndpointTests
    {
        const string m_dummyUrl = "http://dummy.resilientsystems.com";
        UserSessionDto m_session;

        [TestInitialize]
        public void InitRestEndpointTests()
        {
            m_session = new UserSessionDto
            {
                CsrfToken = Guid.NewGuid().ToString()
            };
        }

        [TestMethod]
        public void TestObjectHandleHeader()
        {
            Random rnd = new Random((int)DateTime.UtcNow.Ticks);
            Array.ForEach(GetObjectHandleFormatStrings(), objectHandleType =>
            {
                string expectedHeaderValue = objectHandleType ?? "default";

                Mock<DummyRestEndpoint> mockEndpoint = new Mock<DummyRestEndpoint>(m_session) { CallBase = true };

                // Mock HttpWebRequest so we can provide our own memory stream.  Without it, .Net attempts to connect
                // to the requested URL in order to create the stream, which would fail.
                MemoryStream requestStream = new MemoryStream();
                Mock<HttpWebRequest> mockRequest = new Mock<HttpWebRequest>();
                mockRequest.Setup<Stream>(r => r.GetRequestStream()).Returns(requestStream);

                // The Headers collection needs to be created
                WebHeaderCollection requestHeaders = new WebHeaderCollection();
                mockRequest.SetupGet(r => r.Headers).Returns(requestHeaders);
                mockEndpoint.Protected().Setup<HttpWebRequest>("CreateRequest", ItExpr.IsAny<string>()).Returns(mockRequest.Object);

                // Mock HttpWebResponse
                Mock<HttpWebResponse> mockResponse = new Mock<HttpWebResponse>();
                MemoryStream responseStream = new MemoryStream(System.Text.Encoding.UTF8.GetBytes("{}"));
                mockResponse.Setup<Stream>(r => r.GetResponseStream()).Returns(responseStream);
                
                System.Configuration.ConfigurationManager.AppSettings["Co3HandleFormat"] = objectHandleType;

                bool invoked = false;
                mockEndpoint.Protected().Setup<HttpWebResponse>("GetResponse", ItExpr.IsAny<HttpWebRequest>())
                    .Returns(mockResponse.Object)
                    .Callback((HttpWebRequest request) =>
                    {
                        // this is where we verify the headers
                        Assert.AreEqual(3, requestHeaders.Count);

                        Assert.AreEqual(m_session.CsrfToken, requestHeaders[RestEndpoint.HeaderCsrfToken]);
                        Assert.AreEqual(expectedHeaderValue, requestHeaders[RestEndpoint.HeaderHandleFormat]);
                        Assert.AreEqual("", requestHeaders[RestEndpoint.HeaderTextContentOutputFormat]);

                        // indicate that we've done the testing
                        invoked = true;
                    });

                IncidentDto incident = new IncidentDto
                {
                    CreatorId = new ObjectHandle
                    {
                        Id = Math.Abs(rnd.Next()),
                        Name = Guid.NewGuid().ToString()
                    }
                };
                mockEndpoint.Object.Post<IncidentDto>(m_dummyUrl, incident);

                // verify that the callback was invoked
                Assert.IsTrue(invoked);
            });
        }

        [TestMethod]
        public void TestObjectHandleRequestBody()
        {
            Random rnd = new Random((int)DateTime.UtcNow.Ticks);
            
            Array.ForEach(GetObjectHandleFormatStrings(), objectHandleType =>
            {
                string expectedHeaderValue = objectHandleType ?? "default";

                System.Configuration.ConfigurationManager.AppSettings["Co3HandleFormat"] = objectHandleType;

                DummyRestEndpoint endpoint = new DummyRestEndpoint(m_session);

                IncidentDto incident = new IncidentDto
                {
                    CreatorId = new ObjectHandle
                    {
                        Id = Math.Abs(rnd.Next()),
                        Name = Guid.NewGuid().ToString()
                    }
                };
                
                string expectedJson = null;
                switch (expectedHeaderValue)
                {
                    case "default":
                    case "objects":
                        expectedJson = string.Format("{{\"creator_id\":{{\"id\":{0},\"name\":\"{1}\"}}}}",
                            incident.CreatorId.Id, incident.CreatorId.Name);
                        break;
                    case "ids":
                        expectedJson = string.Format("{{\"creator_id\":{0}}}", incident.CreatorId.Id);
                        break;
                    case "names":
                        expectedJson = string.Format("{{\"creator_id\":\"{0}\"}}", incident.CreatorId.Name);
                        break;
                    default:
                        Assert.Fail();
                        break;
                }

                string json = endpoint.Serialize(incident);
                Assert.AreEqual(expectedJson, json);
            });
        }

        private string[] GetObjectHandleFormatStrings()
        {
            List<string> objectHandleTypes = new List<string>();
            objectHandleTypes.Add(null);
            Array.ForEach((ObjectHandleFormat[])Enum.GetValues(typeof(ObjectHandleFormat)),
                format =>
                {
                    if (format != ObjectHandleFormat.Undefined)
                        objectHandleTypes.Add(RestEndpoint.GetEnumJsonValue(format));
                });
            return objectHandleTypes.ToArray();
        }
    }
}
