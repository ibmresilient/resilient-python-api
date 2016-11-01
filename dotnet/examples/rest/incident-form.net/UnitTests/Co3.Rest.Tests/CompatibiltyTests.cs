using System;
using System.Linq;
using System.Reflection;
using Co3.Rest.Dto;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;

namespace Co3.Rest.Tests
{
    [TestClass]
    public class CompatibilityTests
    {
        [TestMethod]
        public void TestObsoletePropertiesAreMarkedAsJsonIgnore()
        {
            Assembly co3RestAssembly = Assembly.GetAssembly(typeof(IncidentDto));
            Array.ForEach(co3RestAssembly.GetTypes(), type =>
            {
                Array.ForEach(type.GetProperties(), prop =>
                {
                    ObsoleteAttribute obsolete = prop.GetCustomAttribute<ObsoleteAttribute>();
                    if (obsolete != null)
                    {
                        if (prop.GetCustomAttribute<JsonIgnoreAttribute>() == null)
                        {
                            Assert.Fail(string.Format("{0}.{1} is marked as [Obsolete] but is missing [JsonIgnore]",
                                type.Name, prop.Name));
                        }
                    }
                });
            });
        }
    }
}
