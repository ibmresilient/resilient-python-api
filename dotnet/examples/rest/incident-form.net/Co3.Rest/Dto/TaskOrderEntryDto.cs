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

// <auto-generated>
// Generated by <a href="http://enunciate.webcohesion.com">Enunciate</a>.
// </auto-generated>

using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace Co3.Rest.Dto
{
    [JsonObject(MemberSerialization.OptIn)]
    public class TaskOrderEntryDto 
    {
        [JsonProperty("uuid")]
        public string Uuid { get; set; }

        [JsonProperty("at_id")]
        public int AutomaticTaskId { get; set; }

        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("phase_id")]
        public int PhaseId { get; set; }

        [JsonProperty("enabled")]
        public bool Enabled { get; set; }

        /// <summary>
        /// The ID values of incident types that are referenced by actions/rules leading to this task
        /// (typically create task automation).
        /// 
        /// NOTE: This is a carryover from the pre-v27 days where the incident type had a more direct (and exclusive)
        /// bearing on automatic tasks.  We carried it forward for v27 for compatibility, but it should not really be relied
        /// on anymore.
        /// </summary>
        [JsonProperty("incident_type_ids")]
        public List<int> IncidentTypeIds { get; set; }

        [JsonProperty("overridden")]
        public bool Overridden { get; set; }

        [JsonProperty("category_id")]
        public int CategoryId { get; set; }
    }
}