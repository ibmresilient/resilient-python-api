<%@ WebService Language="C#" Class="CMDB.Parks" %>

using System;
using System.Web.Services;
using System.Collections.Generic;
using System.Data;
using System.Linq;
using System.IO;
using System.Reflection;

namespace CMDB
{
    public class ParkData
    {
        public String parkCode;
        public String parkName;
        public double geoLat;
        public double geoLong;
        public bool? hasBlackBear;
        public bool? hasGrizzlyBear;
        public bool? hasPolarBear;
        public String url;
    }

    [WebService (Namespace = "http://tempuri.org/", Description = "A parks web service, with bears")]
    public class Parks
    {
        DataTable data;
        public Parks()
        {
            var reader = Lines("parks.csv");
            data = new DataTable();

            var headers = reader.First().Split(',');
            foreach (var header in headers)
            {
                data.Columns.Add(header);
            }

            var records = reader.Skip(1);
            foreach (var record in records)
            {
                data.Rows.Add(record.Split(','));
            }
        }

        static IEnumerable<string> Lines(string filename)
        {
            using (StreamReader reader = new StreamReader(filename))
                while (!reader.EndOfStream)
                    yield return reader.ReadLine();
        }

        [WebMethod (Description ="Get information about a park")]
        public ParkData GetParkDetails(string parkCode) {
            DataRow[] parks = (from DataRow row in data.Rows
                        where row["parkCode"].Equals(parkCode)
                        select row).ToArray();
            ParkData pd = new ParkData();
            if(parks.Length>0)
            {
                var park = parks[0];
                String f;
                pd.parkCode = park["parkCode"].ToString();
                f = park["parkName"].ToString(); if(f!="") pd.parkName = f;
                f = park["geoLat"].ToString(); if(f!="") pd.geoLat = Double.Parse(f);
                f = park["geoLong"].ToString(); if(f!="") pd.geoLong = Double.Parse(f);
                f = park["hasBlackBear"].ToString(); if(f!="") pd.hasBlackBear = Boolean.Parse(f);
                f = park["hasGrizzlyBear"].ToString(); if(f!="") pd.hasGrizzlyBear = Boolean.Parse(f);
                f = park["hasPolarBear"].ToString(); if(f!="") pd.hasPolarBear = Boolean.Parse(f);
                f = park["url"].ToString(); if(f!="") pd.url = f;
            }
            else
            {
                pd.parkCode = "";
            }
            return pd;
        }
    }
}
