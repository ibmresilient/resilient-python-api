using System;
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Net;
using System.Reflection;
using Co3.Rest.AutoFixture;
using Co3.Rest.Dto;
using Co3.Rest.Endpoints;
using Co3.Rest.Util;
using KellermanSoftware.CompareNetObjects;
using Microsoft.VisualStudio.TestTools.UnitTesting;
using Ploeh.AutoFixture;
using Ploeh.AutoFixture.Kernel;

namespace Co3.Rest
{
    /// <summary>
    /// Tests to verify the DTOs can be serialized and deserialized to the original DTO object.
    /// </summary>
    [TestClass]
    public class SerializationTests
    {
        class Foo
        {
            public MethodName Name { get; set; }
            public bool Value { get; set; }
        }

        [TestMethod]
        public void TestScriptMetadataDtoSerialization()
        {
            ScriptMetadataDto dto = new ScriptMetadataDto
            {
                Keywords = Generator.Generate<List<ScriptMetadataKeywordDto>>(),
                Snippets = Generator.Generate<List<ScriptMetadataSnippetDto>>(),
                Mappings = new Dictionary<string, ScriptMetadataDto>()
            };

            dto.Mappings.Add(Generator.Generate<string>(),
                new ScriptMetadataDto
                {
                    Keywords = Generator.Generate<List<ScriptMetadataKeywordDto>>(),
                    Snippets = Generator.Generate<List<ScriptMetadataSnippetDto>>(),
                    Mappings = new Dictionary<string, ScriptMetadataDto>()
                });
                        
            DummyRestEndpoint endpoint = new DummyRestEndpoint(null);
            string json = endpoint.Serialize(dto);

            ScriptMetadataDto deserializedDto = endpoint.Deserialize<ScriptMetadataDto>(json);

            CompareLogic comparer = new CompareLogic();
            comparer.Compare(dto, deserializedDto);
        }

        [TestMethod]
        public void TestDtoSerialization()
        {
            AssemblyName assembly = Assembly.GetExecutingAssembly().GetReferencedAssemblies().SingleOrDefault(a => a.Name.Equals("Co3.Rest"));
            if (assembly != null)
            {
                CompareLogic comparer = new CompareLogic();
                DummyRestEndpoint endpoint = new DummyRestEndpoint(null);
                foreach (Type type in Assembly.Load(assembly).GetTypes()
                    .Where(t => t.IsClass && t.Namespace.EndsWith(".Dto") && !t.IsAbstract))
                {
                    // AutoFixture has trouble populating ScriptMetadataDto
                    // so we'll test it separately.
                    if (type.Name == "ScriptMetadataDto")
                    {
                        System.Diagnostics.Debug.WriteLine("Skipping " + type.FullName);
                        return;
                    }

                    System.Diagnostics.Debug.WriteLine(type.FullName);

                    string typeName = type.Name;
                    object dto = Generator.Generate(type);
                    string json = endpoint.Serialize(dto);
                    object deserialized = endpoint.Deserialize(json, type);

                    comparer.Compare(dto, deserialized);
                }
            }
        }
    }
}
