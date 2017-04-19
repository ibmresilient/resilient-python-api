﻿using System;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using Co3.Rest.Dto;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Newtonsoft.Json;
using Newtonsoft.Json.Converters;

namespace Co3.Rest
{
    [TestClass]
    public class CompatibilityTests
    {
        [TestMethod]
        public void TestEnumsHaveStringEnumConverterAttribute()
        {
            var assembly = Assembly.GetExecutingAssembly().GetReferencedAssemblies().SingleOrDefault(a => a.Name.Equals("Co3.Rest"));
            if (assembly != null)
            {
                foreach (Type type in Assembly.Load(assembly).GetTypes().Where(t => t.IsEnum))
                {
                    if (type.GetMembers().Any(m => m.MemberType == MemberTypes.Field && m.IsDefined(typeof (EnumMemberAttribute))))
                    {
                        JsonConverterAttribute jsonConverterAttribute = type.GetCustomAttribute<JsonConverterAttribute>();
                        if (jsonConverterAttribute == null || jsonConverterAttribute.ConverterType != typeof (StringEnumConverter))
                        {
                            Assert.Fail("{0} enum is missing [JsonConverter] attribute", type.Name);
                        }
                    }
                }
            }
        }
    }
}