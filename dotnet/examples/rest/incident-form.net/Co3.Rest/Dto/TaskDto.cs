/*
 * Co3 Systems, Inc. ("Co3") is willing to license software or access to 
 * software to the company or entity that will be using or accessing the 
 * software and documentation and that you represent as an employee or 
 * authorized agent ("you" or "your" only on the condition that you 
 * accept all of the terms of this license agreement.
 *
 * The software and documentation within Co3's Development Kit are 
 * copyrighted by and contain confidential information of Co3. By 
 * accessing and/or using this software and documentation, you agree 
 * that while you may make derivative works of them, you:
 * 
 * 1)   will not use the software and documentation or any derivative 
 *      works for anything but your internal business purposes in 
 *      conjunction your licensed used of Co3's software, nor
 * 2)   provide or disclose the software and documentation or any 
 *      derivative works to any third party.
 * 
 * THIS SOFTWARE AND DOCUMENTATION IS PROVIDED "AS IS" AND ANY EXPRESS 
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED 
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
 * ARE DISCLAIMED. IN NO EVENT SHALL CO3 BE LIABLE FOR ANY DIRECT, 
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
    public class TaskDto
    {
        [JsonProperty("inc_name")]
        public string IncName { get; set; }

        [JsonProperty("name")]
        public string Name { get; set; }

        [JsonProperty("regs")]
        public SortedList<string, string> Regs { get; set; }

        [JsonProperty("custom")]
        public bool Custom { get; set; }

        [JsonProperty("inc_id")]
        public int IncId { get; set; }

        [JsonProperty("inc_owner_id")]
        public int IncOwnerId { get; set; }

        [JsonProperty("rollup_id")]
        public int RollupId { get; set; }

        [JsonProperty("due_date")]
        public DateTime DueDate { get; set; }

        [JsonProperty("required")]
        public bool Required { get; set; }

        [JsonProperty("owner_id")]
        public int OwnerId { get; set; }

        [JsonProperty("id")]
        public int Id { get; set; }

        [JsonProperty("status")]
        public string Status { get; set; }

        [JsonProperty("inc_training")]
        public bool IncTraining { get; set; }

        [JsonProperty("frozen")]
        public bool Frozen { get; set; }

        [JsonProperty("owner_fname")]
        public string OwnerFname { get; set; }

        [JsonProperty("owner_lname")]
        public string OwnerLname { get; set; }

        [JsonProperty("cat_name")]
        public string CatName { get; set; }

        [JsonProperty("description")]
        public string Description { get; set; }

        [JsonProperty("init_date")]
        public DateTime InitDate { get; set; }

        [JsonProperty("src_name")]
        public string SrcName { get; set; }

        [JsonProperty("instr_text")]
        public string InstrText { get; set; }

        [JsonProperty("auto_task_id")]
        public int AutoTaskId { get; set; }

        [JsonProperty("active")]
        public bool Active { get; set; }

        [JsonProperty("members")]
        public List<int> Members { get; set; }

        [JsonProperty("perms")]
        public TaskPermsDto Perms { get; set; }

        [JsonProperty("creator")]
        public JustUserDto Creator { get; set; }

        [JsonProperty("notes")]
        public List<TaskCommentDto> Notes { get; set; }

        [JsonProperty("closed_date")]
        public DateTime ClosedDate { get; set; }
    }
}
