

using System;
using Co3.Rest.Dto;
using Co3.Rest.JsonConverters;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;

namespace Co3.Rest.JsonConverters
{
    [TestClass]
    public class ObjectHandlerConverterTests
    {
        private JsonSerializerSettings m_jsonSerializerSettings;

        [TestInitialize]
        public void InitObjectHandlerConverterTests()
        {
            m_jsonSerializerSettings = new JsonSerializerSettings()
            {
                DefaultValueHandling = DefaultValueHandling.Ignore,
                NullValueHandling = NullValueHandling.Ignore
            };
        }

        [TestMethod]
        public void TestSerializeIds()
        {
            SerializeAndVerify(ObjectHandleFormat.Ids);
        }

        [TestMethod]
        public void TestSerializeNames()
        {
            SerializeAndVerify(ObjectHandleFormat.Names);
        }

        [TestMethod]
        public void TestSerializeObjects()
        {
            SerializeAndVerify(ObjectHandleFormat.Objects);
        }

        private void SerializeAndVerify(ObjectHandleFormat format)
        {
            m_jsonSerializerSettings.Converters.Add(new ObjectHandleConverter(format));

            ObjectHandle handle = new ObjectHandle
            {
                Id = 123,
                Name = "one two three"
            };

            string expectedJson;
            switch (format)
            {
                case ObjectHandleFormat.Ids:
                    expectedJson = handle.Id.ToString();
                    break;
                case ObjectHandleFormat.Names:
                    expectedJson = string.Format("\"{0}\"", handle.Name);
                    break;
                case ObjectHandleFormat.Objects:
                    expectedJson = string.Format("{{\"id\":{0},\"name\":\"{1}\"}}", handle.Id, handle.Name);
                    break;
                default:
                    throw new NotImplementedException();
            }

            string json = JsonConvert.SerializeObject(handle, m_jsonSerializerSettings);
            Assert.AreEqual(expectedJson, json);
        }
    }
}
