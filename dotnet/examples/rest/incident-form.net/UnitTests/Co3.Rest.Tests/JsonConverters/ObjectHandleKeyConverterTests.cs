using System;
using System.Collections.Generic;
using Co3.Rest.Dto;
using Co3.Rest.Endpoints;
using KellermanSoftware.CompareNetObjects;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace Co3.Rest.JsonConverters
{
    [TestClass]
    public class UnitTest1
    {
        [TestMethod]
        public void TestSerialization()
        {
            DataTableRowDataDto dto = new DataTableRowDataDto
            {
                Cells = new System.Collections.Generic.Dictionary<ObjectHandle, DataTableCellDataDto>()
            };

            ObjectHandle handle = new ObjectHandle
            {
                Name = "one_two_three"
            };

            dto.Cells.Add(handle, new DataTableCellDataDto
            {
                Id = new ObjectHandle { Id = 1 },
                RowId = 2,
                Value = "value"
            });

            DummyRestEndpoint rest = new DummyRestEndpoint(null);
            string json = rest.Serialize(dto);
            DataTableRowDataDto deserialized = rest.Deserialize<DataTableRowDataDto>(json);

            CompareLogic comparer = new CompareLogic();
            comparer.Compare(dto, deserialized);
        }
    }
}
