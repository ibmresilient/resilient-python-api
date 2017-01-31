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
    ///  Defines the permissions available to the caller on a given field. This object is returned with each field object retrieved by the caller.
    /// </summary>
    public class FieldDefPermsDto
    {

        /// <summary>
        ///  True if this field can be deleted, false otherwise
        /// </summary>
        [JsonProperty("delete")]
        public bool Delete { get; set; }

        /// <summary>
        ///  True if the name of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_name")]
        public bool ModifyName { get; set; }

        /// <summary>
        ///  True if the values of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_values")]
        public bool ModifyValues { get; set; }

        /// <summary>
        ///  True if the blank option of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_blank")]
        public bool ModifyBlank { get; set; }

        /// <summary>
        ///  True if the requiredness of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_required")]
        public bool ModifyRequired { get; set; }

        /// <summary>
        ///  True if the operations of this field can be modified, false otherwise.
        /// </summary>
        [JsonProperty("modify_operations")]
        public bool ModifyOperations { get; set; }

        /// <summary>
        ///  True if the chosen attribute of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_chosen")]
        public bool ModifyChosen { get; set; }

        /// <summary>
        ///  True if the default value of this field can be modified, false otherwise
        /// </summary>
        [JsonProperty("modify_default")]
        public bool ModifyDefault { get; set; }

        /// <summary>
        ///  The other types that this field can be changed to. e.g. select -> multiselect
        /// </summary>
        [JsonProperty("modify_type")]
        public List<InputType> ModifyType { get; set; }

        /// <summary>
        ///  True if this field can be sorted, false otherwise
        /// </summary>
        [JsonProperty("sort")]
        public bool Sort { get; set; }

        /// <summary>
        /// </summary>
        [JsonProperty("show_in_manual_actions")]
        public bool ShowInManualActions { get; set; }
        
        /// <summary>
        /// </summary>
        [JsonProperty("show_in_auto_actions")]
        public bool ShowInAutomaticActions { get; set; }
        
        [Obsolete]
        [JsonIgnore]
        public bool ShowInAutoActions
        {
            get { return ShowInAutomaticActions; }
            set { ShowInAutomaticActions = value; }
        }

        /// <summary>
        /// </summary>
        [JsonProperty("show_in_notifications")]
        public bool ShowInNotifications { get; set; }

    }
}
