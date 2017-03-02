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
using System.IO;
using System.Linq;
using System.Windows.Forms;
using Co3.Rest;
using Co3.Rest.Dto;

namespace BulkAddFieldValues
{
    public partial class AppFrame : Form
    {
        private SessionRest m_sessionRest;
        private UserSessionDto m_session;

        public AppFrame()
        {
            InitializeComponent();

            m_sessionRest = null;

            ApiUrl.Text = RestEndpoint.Co3ApiUrl;
            UserEmail.Text = System.Configuration.ConfigurationManager.AppSettings["Email"];
        }

        private bool HasCredentials
        {
            get
            {
                return !string.IsNullOrEmpty(ApiUrl.Text)
                    && !string.IsNullOrEmpty(ApiUrl.Text.Trim())
                    && !string.IsNullOrEmpty(UserEmail.Text)
                    && !string.IsNullOrEmpty(UserEmail.Text.Trim())
                    && !string.IsNullOrEmpty(Password.Text);
            }
        }

        private void OnCredentialsChanged(object sender, EventArgs e)
        {
            ConnectBtn.Enabled = HasCredentials;
        }

        private void ConnectBtn_Click(object sender, EventArgs e)
        {
            RestEndpoint.Co3ApiUrl = ApiUrl.Text.Trim();
            AuthenticationDto credentials = new AuthenticationDto
            {
                Email = UserEmail.Text.Trim(),
                Password = Password.Text
            };

            m_sessionRest = new SessionRest();
            try
            {
                m_session = m_sessionRest.Authenticate(credentials);
                if (m_session == null)
                    return;
            }
            catch
            {
                MessageBox.Show("Invalid user credentials or API URL", "Authentication Error", MessageBoxButtons.OK);
                return;
            }

            Orgs.Items.Clear();
            foreach (SessionOrgInfoDto sessionOrgInfoDto in m_session.Orgs)
            {
                Orgs.Items.Add(sessionOrgInfoDto);
            }

            Orgs.SelectedIndex = 0;
            Orgs_SelectedIndexChanged(sender, e);

            Orgs.Enabled = true;
            FieldNames.Enabled = true;
            ValuesFile.Enabled = true;
            BrowseBtn.Enabled = true;
            OnFieldDataChanged(sender, e);
        }

        private void Orgs_SelectedIndexChanged(object sender, EventArgs e)
        {
            FieldNames.Items.Clear();
            FieldRest fieldRest = m_sessionRest.GetFieldRest();
            FieldDefDto[] vecFields = fieldRest.GetFieldTypes(((SessionOrgInfoDto)Orgs.SelectedItem).Id);
            foreach (FieldDefDto fieldDefDto in vecFields)
            {
                if (fieldDefDto.Internal
                    || fieldDefDto.InputType != InputType.MultiSelect
                    && fieldDefDto.InputType != InputType.Select)
                {
                    continue;
                }

                FieldNames.Items.Add(fieldDefDto);
            }
        }

        private void BrowseBtn_Click(object sender, EventArgs e)
        {
            using (OpenFileDialog dlg = new OpenFileDialog())
            {
                dlg.ShowDialog();
                ValuesFile.Text = dlg.FileName;
            }
            OnFieldDataChanged(sender, e);
        }

        private void OnFieldDataChanged(object sender, EventArgs e)
        {
            SaveBtn.Enabled = Orgs.Items.Count > 0 && FieldNames.Items.Count > 0
                && FieldNames.SelectedIndex >= 0
                && !string.IsNullOrEmpty(ValuesFile.Text);
        }

        private void SaveBtn_Click(object sender, EventArgs e)
        {
            if (!File.Exists(ValuesFile.Text))
            {
                MessageBox.Show(string.Format("\"{0}\" does not exist", ValuesFile.Text));
                return;
            }

            string[] vecLines;

            try
            {
                vecLines = File.ReadAllLines(ValuesFile.Text);
            }
            catch (Exception ex)
            {
                MessageBox.Show(string.Format("Error reading file: {0}", ex.Message));
                return;
            }

            if (vecLines.Length == 0)
            {
                MessageBox.Show("File contains no data");
                return;
            }

            FieldDefDto field = (FieldDefDto)FieldNames.SelectedItem;

            // cache existing values for faster lookup
            Dictionary<string, FieldDefValueDto> mapExistingValues = field.Values.ToDictionary(fieldDefValueDto => fieldDefValueDto.Label.ToLower());


            foreach (string line in vecLines)
            {
                if (!string.IsNullOrEmpty(line))
                {
                    string strValue = line.Trim();
                    if (!string.IsNullOrEmpty(strValue)
                        && !mapExistingValues.ContainsKey(strValue.ToLower()))
                    {
                        field.Values.Add(new FieldDefValueDto { Label = strValue });
                    }
                }
            }

            // we added values, save them
            if (field.Values.Count == mapExistingValues.Count)
            {
                MessageBox.Show("Data file contains no new field values");
                return;
            }

            try
            {
                FieldRest fieldRest = m_sessionRest.GetFieldRest();
                FieldDefDto savedField = fieldRest.SaveField(((SessionOrgInfoDto)Orgs.SelectedItem).Id, field);

                if (savedField.Id == field.Id)
                {
                    // save the updated field back to the dropdown list so that
                    // it would contain the new values
                    FieldNames.Items[FieldNames.SelectedIndex] = savedField;

                    MessageBox.Show(string.Format("Added new values to field \"{0}\"", field.Name));
                    return;
                }

                MessageBox.Show("Failed to save field values");
            }
            catch (Exception ex)
            {
                MessageBox.Show(ex.Message);
            }
        }

    }
}
