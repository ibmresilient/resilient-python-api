using System;
using System.Collections;
using System.Collections.Generic;
using Co3.Rest.Util;
using Ploeh.AutoFixture.Kernel;

namespace Co3.Rest.AutoFixture
{
    public class EnumGenerator : ISpecimenBuilder
    {
        public object Create(object request, ISpecimenContext context)
        {
            Type type = request as Type;

            if (type == null)
            {
                SeededRequest seeded = request as SeededRequest;
                if (seeded == null || (type = seeded.Request as Type) == null)
                    return new NoSpecimen();
            }

            if (!type.IsEnum)
                return new NoSpecimen();

            IEnumerator it = Enum.GetValues(type).GetEnumerator();
            List<object> availableEnums = new List<object>();
            while (it.MoveNext())
            {
                if (EnumUtil.GetEnumMemberValue(type, it.Current) != null)
                    availableEnums.Add(it.Current);
            }

            if (availableEnums.Count > 0)
                return availableEnums[Generator.Generate<int>() % availableEnums.Count];

            return new NoSpecimen();
        }
    }
}
