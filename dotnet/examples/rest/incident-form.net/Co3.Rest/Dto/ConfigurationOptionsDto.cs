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
    ///  Contains all of the selected configuration choices for export.
    /// </summary>
    public class ConfigurationOptionsDto
    {

        /// <summary>
        ///  When true it means that phases and tasks are exported.
        /// </summary>
        [JsonProperty("phases_and_tasks")]
        public bool PhasesAndTasks { get; set; }

        /// <summary>
        ///  When true it means that actions, message destinations, and custom action views are exported.
        /// </summary>
        [JsonProperty("actions")]
        public bool Actions { get; set; }

        /// <summary>
        ///  When true it means that the customized layouts are exported.
        /// </summary>
        [JsonProperty("layouts")]
        public bool Layouts { get; set; }

        /// <summary>
        ///  When true it means that the notification definitions are exported.
        /// </summary>
        [JsonProperty("notifications")]
        public bool Notifications { get; set; }

        /// <summary>
        ///  When true it means that the timeframes are exported.
        /// </summary>
        [JsonProperty("timeframes")]
        public bool Timeframes { get; set; }

        /// <summary>
        ///  When true it means the breach data are exported.
        /// </summary>
        [JsonProperty("breach_data")]
        public bool BreachData { get; set; }

    }
}
