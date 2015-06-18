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

namespace BulkAddFieldValues
{
    partial class AppFrame
    {
        /// <summary>
        /// Required designer variable.
        /// </summary>
        private System.ComponentModel.IContainer components = null;

        /// <summary>
        /// Clean up any resources being used.
        /// </summary>
        /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
        protected override void Dispose(bool disposing)
        {
            if (disposing && (components != null))
            {
                components.Dispose();
            }
            base.Dispose(disposing);
        }

        #region Windows Form Designer generated code

        /// <summary>
        /// Required method for Designer support - do not modify
        /// the contents of this method with the code editor.
        /// </summary>
        private void InitializeComponent()
        {
            System.ComponentModel.ComponentResourceManager resources = new System.ComponentModel.ComponentResourceManager(typeof(AppFrame));
            this.label1 = new System.Windows.Forms.Label();
            this.label2 = new System.Windows.Forms.Label();
            this.UserEmail = new System.Windows.Forms.TextBox();
            this.Password = new System.Windows.Forms.TextBox();
            this.label3 = new System.Windows.Forms.Label();
            this.ApiUrl = new System.Windows.Forms.TextBox();
            this.label4 = new System.Windows.Forms.Label();
            this.FieldNames = new System.Windows.Forms.ComboBox();
            this.label5 = new System.Windows.Forms.Label();
            this.ValuesFile = new System.Windows.Forms.TextBox();
            this.BrowseBtn = new System.Windows.Forms.Button();
            this.SaveBtn = new System.Windows.Forms.Button();
            this.groupBox1 = new System.Windows.Forms.GroupBox();
            this.ConnectBtn = new System.Windows.Forms.Button();
            this.groupBox2 = new System.Windows.Forms.GroupBox();
            this.Orgs = new System.Windows.Forms.ComboBox();
            this.label6 = new System.Windows.Forms.Label();
            this.groupBox1.SuspendLayout();
            this.groupBox2.SuspendLayout();
            this.SuspendLayout();
            // 
            // label1
            // 
            this.label1.AutoSize = true;
            this.label1.Location = new System.Drawing.Point(24, 48);
            this.label1.Name = "label1";
            this.label1.Size = new System.Drawing.Size(59, 13);
            this.label1.TabIndex = 0;
            this.label1.Text = "User email:";
            // 
            // label2
            // 
            this.label2.AutoSize = true;
            this.label2.Location = new System.Drawing.Point(27, 74);
            this.label2.Name = "label2";
            this.label2.Size = new System.Drawing.Size(56, 13);
            this.label2.TabIndex = 1;
            this.label2.Text = "Password:";
            // 
            // UserEmail
            // 
            this.UserEmail.Location = new System.Drawing.Point(89, 45);
            this.UserEmail.Name = "UserEmail";
            this.UserEmail.Size = new System.Drawing.Size(300, 20);
            this.UserEmail.TabIndex = 2;
            this.UserEmail.TextChanged += new System.EventHandler(this.OnCredentialsChanged);
            // 
            // Password
            // 
            this.Password.Location = new System.Drawing.Point(89, 71);
            this.Password.Name = "Password";
            this.Password.Size = new System.Drawing.Size(300, 20);
            this.Password.TabIndex = 3;
            this.Password.UseSystemPasswordChar = true;
            this.Password.TextChanged += new System.EventHandler(this.OnCredentialsChanged);
            // 
            // label3
            // 
            this.label3.AutoSize = true;
            this.label3.Location = new System.Drawing.Point(17, 22);
            this.label3.Name = "label3";
            this.label3.Size = new System.Drawing.Size(66, 13);
            this.label3.TabIndex = 4;
            this.label3.Text = "Server URL:";
            // 
            // ApiUrl
            // 
            this.ApiUrl.Location = new System.Drawing.Point(89, 19);
            this.ApiUrl.Name = "ApiUrl";
            this.ApiUrl.Size = new System.Drawing.Size(300, 20);
            this.ApiUrl.TabIndex = 1;
            this.ApiUrl.TextChanged += new System.EventHandler(this.OnCredentialsChanged);
            // 
            // label4
            // 
            this.label4.AutoSize = true;
            this.label4.Location = new System.Drawing.Point(27, 49);
            this.label4.Name = "label4";
            this.label4.Size = new System.Drawing.Size(61, 13);
            this.label4.TabIndex = 6;
            this.label4.Text = "Field name:";
            // 
            // FieldNames
            // 
            this.FieldNames.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.FieldNames.Enabled = false;
            this.FieldNames.FormattingEnabled = true;
            this.FieldNames.Location = new System.Drawing.Point(94, 46);
            this.FieldNames.Name = "FieldNames";
            this.FieldNames.Size = new System.Drawing.Size(295, 21);
            this.FieldNames.TabIndex = 6;
            // 
            // label5
            // 
            this.label5.AutoSize = true;
            this.label5.Location = new System.Drawing.Point(6, 76);
            this.label5.Name = "label5";
            this.label5.Size = new System.Drawing.Size(82, 13);
            this.label5.TabIndex = 8;
            this.label5.Text = "Field values file:";
            // 
            // ValuesFile
            // 
            this.ValuesFile.Enabled = false;
            this.ValuesFile.Location = new System.Drawing.Point(94, 73);
            this.ValuesFile.Name = "ValuesFile";
            this.ValuesFile.Size = new System.Drawing.Size(214, 20);
            this.ValuesFile.TabIndex = 7;
            this.ValuesFile.TextChanged += new System.EventHandler(this.OnFieldDataChanged);
            // 
            // BrowseBtn
            // 
            this.BrowseBtn.Enabled = false;
            this.BrowseBtn.Location = new System.Drawing.Point(314, 71);
            this.BrowseBtn.Name = "BrowseBtn";
            this.BrowseBtn.Size = new System.Drawing.Size(75, 23);
            this.BrowseBtn.TabIndex = 8;
            this.BrowseBtn.Text = "Browse ...";
            this.BrowseBtn.UseVisualStyleBackColor = true;
            this.BrowseBtn.Click += new System.EventHandler(this.BrowseBtn_Click);
            // 
            // SaveBtn
            // 
            this.SaveBtn.Enabled = false;
            this.SaveBtn.Location = new System.Drawing.Point(314, 103);
            this.SaveBtn.Name = "SaveBtn";
            this.SaveBtn.Size = new System.Drawing.Size(75, 23);
            this.SaveBtn.TabIndex = 9;
            this.SaveBtn.Text = "Save";
            this.SaveBtn.UseVisualStyleBackColor = true;
            this.SaveBtn.Click += new System.EventHandler(this.SaveBtn_Click);
            // 
            // groupBox1
            // 
            this.groupBox1.Controls.Add(this.ConnectBtn);
            this.groupBox1.Controls.Add(this.label3);
            this.groupBox1.Controls.Add(this.label1);
            this.groupBox1.Controls.Add(this.label2);
            this.groupBox1.Controls.Add(this.ApiUrl);
            this.groupBox1.Controls.Add(this.UserEmail);
            this.groupBox1.Controls.Add(this.Password);
            this.groupBox1.Location = new System.Drawing.Point(12, 12);
            this.groupBox1.Name = "groupBox1";
            this.groupBox1.Size = new System.Drawing.Size(395, 128);
            this.groupBox1.TabIndex = 12;
            this.groupBox1.TabStop = false;
            this.groupBox1.Text = "User Credentials";
            // 
            // ConnectBtn
            // 
            this.ConnectBtn.Enabled = false;
            this.ConnectBtn.Location = new System.Drawing.Point(314, 97);
            this.ConnectBtn.Name = "ConnectBtn";
            this.ConnectBtn.Size = new System.Drawing.Size(75, 23);
            this.ConnectBtn.TabIndex = 4;
            this.ConnectBtn.Text = "Connect";
            this.ConnectBtn.UseVisualStyleBackColor = true;
            this.ConnectBtn.Click += new System.EventHandler(this.ConnectBtn_Click);
            // 
            // groupBox2
            // 
            this.groupBox2.Controls.Add(this.Orgs);
            this.groupBox2.Controls.Add(this.label6);
            this.groupBox2.Controls.Add(this.FieldNames);
            this.groupBox2.Controls.Add(this.BrowseBtn);
            this.groupBox2.Controls.Add(this.SaveBtn);
            this.groupBox2.Controls.Add(this.ValuesFile);
            this.groupBox2.Controls.Add(this.label4);
            this.groupBox2.Controls.Add(this.label5);
            this.groupBox2.Location = new System.Drawing.Point(12, 146);
            this.groupBox2.Name = "groupBox2";
            this.groupBox2.Size = new System.Drawing.Size(395, 137);
            this.groupBox2.TabIndex = 13;
            this.groupBox2.TabStop = false;
            this.groupBox2.Text = "Field Values";
            // 
            // Orgs
            // 
            this.Orgs.DropDownStyle = System.Windows.Forms.ComboBoxStyle.DropDownList;
            this.Orgs.Enabled = false;
            this.Orgs.FormattingEnabled = true;
            this.Orgs.Location = new System.Drawing.Point(94, 19);
            this.Orgs.Name = "Orgs";
            this.Orgs.Size = new System.Drawing.Size(295, 21);
            this.Orgs.TabIndex = 5;
            this.Orgs.SelectedIndexChanged += new System.EventHandler(this.Orgs_SelectedIndexChanged);
            // 
            // label6
            // 
            this.label6.AutoSize = true;
            this.label6.Location = new System.Drawing.Point(19, 22);
            this.label6.Name = "label6";
            this.label6.Size = new System.Drawing.Size(69, 13);
            this.label6.TabIndex = 12;
            this.label6.Text = "Organization:";
            // 
            // AppFrame
            // 
            this.AutoScaleDimensions = new System.Drawing.SizeF(6F, 13F);
            this.AutoScaleMode = System.Windows.Forms.AutoScaleMode.Font;
            this.ClientSize = new System.Drawing.Size(419, 295);
            this.Controls.Add(this.groupBox2);
            this.Controls.Add(this.groupBox1);
            this.Icon = ((System.Drawing.Icon)(resources.GetObject("$this.Icon")));
            this.Name = "AppFrame";
            this.Text = "Bulk Add Field Values";
            this.groupBox1.ResumeLayout(false);
            this.groupBox1.PerformLayout();
            this.groupBox2.ResumeLayout(false);
            this.groupBox2.PerformLayout();
            this.ResumeLayout(false);

        }

        #endregion

        private System.Windows.Forms.Label label1;
        private System.Windows.Forms.Label label2;
        private System.Windows.Forms.TextBox UserEmail;
        private System.Windows.Forms.TextBox Password;
        private System.Windows.Forms.Label label3;
        private System.Windows.Forms.TextBox ApiUrl;
        private System.Windows.Forms.Label label4;
        private System.Windows.Forms.ComboBox FieldNames;
        private System.Windows.Forms.Label label5;
        private System.Windows.Forms.TextBox ValuesFile;
        private System.Windows.Forms.Button BrowseBtn;
        private System.Windows.Forms.Button SaveBtn;
        private System.Windows.Forms.GroupBox groupBox1;
        private System.Windows.Forms.Button ConnectBtn;
        private System.Windows.Forms.GroupBox groupBox2;
        private System.Windows.Forms.ComboBox Orgs;
        private System.Windows.Forms.Label label6;
    }
}

