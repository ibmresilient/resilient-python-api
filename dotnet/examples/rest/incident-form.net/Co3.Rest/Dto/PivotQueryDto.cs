/*
 * Resilient Systems, Inc. ("Resilient") is willing to license software
 * or access to software to the company or entity that will be using or
 * accessing the software and documentation and that you represent as
 * an employee or authorized agent ("you" or "your") only on the condition
 * that you accept all of the terms of this license agreement.
 *
 * The software and documentation within Resilient's Development Kit are
 * copyrighted by and contain confidential information of Resilient. By
 * accessing and/or using this software and documentation, you agree that
 * while you may make derivative works of them, you:
 *
 * 1)  will not use the software and documentation or any derivative
 *     works for anything but your internal business purposes in
 *     conjunction your licensed used of Resilient's software, nor
 * 2)  provide or disclose the software and documentation or any
 *     derivative works to any third party.
 *
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED. IN NO EVENT SHALL RESILIENT BE LIABLE FOR ANY DIRECT,
 * INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
 * (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
 * HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT,
 * STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
 * ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED
 * OF THE POSSIBILITY OF SUCH DAMAGE.
 */

using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Co3.Rest.Dto
{
    /// <summary>
    ///  Contains all the necessary data to perform a pivot on an object type
    /// </summary>
    public class PivotQueryDto
    {

        /// <summary>
        ///  The filters to apply to the query which will be performed to determine the data set for the pivot.
        /// </summary>
        [JsonProperty("filters")]
        public List<QueryFilterDto> Filters { get; set; }

        /// <summary>
        ///  The fields which will appear in the rows for the pivot table
        /// </summary>
        [JsonProperty("row_fields")]
        public List<PivotFieldDto> RowFields { get; set; }

        /// <summary>
        ///  The fields which will appear in the columns for the pivot table
        /// </summary>
        [JsonProperty("column_fields")]
        public List<PivotFieldDto> ColumnFields { get; set; }

        /// <summary>
        ///  The function which will be applied to the cell contents of the pivot table
        /// </summary>
        [JsonProperty("function")]
        public FunctionDto Function { get; set; }

        /// <summary>
        ///  The timezone offset in minutes which will be used to modify date values to be in the appropriate timezone. A positive value for timezones before UTC and a negative value for timezones after UTC
        /// </summary>
        [JsonProperty("offset")]
        public int Offset { get; set; }

    }
}
