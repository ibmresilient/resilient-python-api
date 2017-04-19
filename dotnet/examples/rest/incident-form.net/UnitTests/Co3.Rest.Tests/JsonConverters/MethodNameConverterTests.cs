using System;
using System.Collections.Generic;
using Co3.Rest.Dto;
using Co3.Rest.Util;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;

namespace Co3.Rest.JsonConverters
{
    [TestClass]
    public class MethodNameConverterTests
    {
        private JsonSerializerSettings m_jsonSerializerSettings;

        [TestInitialize]
        public void InitMethodNameConverterTests()
        {
            m_jsonSerializerSettings = new JsonSerializerSettings()
            {
                DefaultValueHandling = DefaultValueHandling.Ignore,
                NullValueHandling = NullValueHandling.Ignore
            };

            m_jsonSerializerSettings.Converters.Add(new MethodNameKeyConverter<int>());
        }

        [TestMethod]
        public void TestLowerCases()
        {
            VerifyMethodNameKeys(value => value);
        }

        delegate string CaseDelegate(string value);

        /// <summary>
        /// DE2349: If the MethodName is used as a key in a map, then it would be in all caps.
        /// This converter works around that problem.  It should be removed when the bug is fixed.
        /// </summary>
        [TestMethod]
        public void TestUpperCases()
        {
            VerifyMethodNameKeys(value => value.ToUpper());
        }
        
        private void VerifyMethodNameKeys(CaseDelegate caseDelegate)
        {
            Type type = typeof(MethodName);

            // Generate a map based on all the MethodName enums
            SortedList<string, int> map = new SortedList<string, int>();
            foreach (MethodName name in Enum.GetValues(type))
            {
                if (name == MethodName.Undefined)
                    continue;

                map.Add(caseDelegate(EnumUtil.GetEnumMemberValue(type, name)), map.Count + 1);
            }

            // Convert the map into JSON
            string json = JsonConvert.SerializeObject(map);
            
            // Convert the JSON back to the map
            Dictionary<MethodName, int> deserializedMap = JsonConvert.DeserializeObject<Dictionary<MethodName, int>>(json,
                m_jsonSerializerSettings);

            // Check that everything is the same
            Assert.AreEqual(map.Count, deserializedMap.Count);
            foreach (MethodName name in Enum.GetValues(type))
            {
                if (name == MethodName.Undefined)
                    continue;

                Assert.IsTrue(deserializedMap.ContainsKey(name));
            }
        }
    }
}
