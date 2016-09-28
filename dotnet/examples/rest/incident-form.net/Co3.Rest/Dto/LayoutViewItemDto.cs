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
    ///  Represents an item inside a view.
    /// </summary>
    public class LayoutViewItemDto
    {

        /// <summary>
        ///  The step label (if applicable).
        /// </summary>
        [JsonProperty("step_label")]
        public string StepLabel { get; set; }

        /// <summary>
        ///  The list of fields in the view.
        /// </summary>
        [JsonProperty("fields")]
        public List<LayoutViewItemDto> Fields { get; set; }

        /// <summary>
        ///  List of conditions that must be true in order to show the view (applicable only for items with an "element" property value of "section").
        /// </summary>
        [JsonProperty("show_if")]
        public List<LayoutViewConditionDto> ShowIf { get; set; }

        /// <summary>
        ///  Gets the element.  This can be one of: field - the item is a field reference.  The field name is stored in the content property. html - the item is an HTML block.  The HTML content is stored in the content property. header - the item is a header.  The header text is stored in the content property. section - the item is a section.  The content property is ignored.  The list of sub-items is stored in the "fields" property. tab - the item is a tab.  The content property is ignored.  The list of sub-items (sections, fields, etc.) is stored in the "fields" property.
        /// </summary>
        [JsonProperty("element")]
        public string Element { get; set; }

        /// <summary>
        ///  The type of object to which this view item applies.  Currently, the following values are supported: incident actioninvocation
        /// </summary>
        [JsonProperty("field_type")]
        public string FieldType { get; set; }

        /// <summary>
        ///  The content for the item.  The value here depends on the element property (see the list of possible element property values).
        /// </summary>
        [JsonProperty("content")]
        public string Content { get; set; }

        /// <summary>
        ///  Some of the items are "predefined" by the server.  We give them a well-known UUID so users can reset back to the known state.
        /// </summary>
        [JsonProperty("predefined_uuid")]
        public string PredefinedUuid { get; set; }

        /// <summary>
        ///  Link header should be displayed or not. This property is for UI side use only
        /// </summary>
        [JsonProperty("show_link_header")]
        public bool ShowLinkHeader { get; set; }

    }
}
